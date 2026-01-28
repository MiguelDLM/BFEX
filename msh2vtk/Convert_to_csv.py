import os
import numpy as np
import pandas as pd
import gmsh
import json
import pyvista as pv
from pyvista import _vtk as vtk
import argparse
import sys
#import cupy as cp

def find_msh_files(python_file, workspace_hint=None):
    folder_path = os.path.splitext(python_file)[0]
    
    # Strategy to find the correct folder:
    # 1. If workspace_hint is provided, check if MSH files are there
    if workspace_hint and os.path.isdir(workspace_hint):
        if os.path.exists(os.path.join(workspace_hint, 'mesh.msh')):
            folder_path = workspace_hint
            
    # 2. Check the default location (same name as script, same dir)
    mesh_file = os.path.join(folder_path, 'mesh.msh')
    
    # 3. If not found, check if it's in a 'workspace' subdirectory (common pattern)
    if not os.path.exists(mesh_file):
        base_name = os.path.splitext(os.path.basename(python_file))[0]
        parent_dir = os.path.dirname(python_file)
        
        # Check ../workspace/base_name (relative to script)
        alt_path = os.path.join(parent_dir, 'workspace', base_name)
        if os.path.exists(os.path.join(alt_path, 'mesh.msh')):
            folder_path = alt_path
            
        # Check ../../workspace/base_name (relative to script, if script is in model folder)
        # This covers cases where repo structure is more complex
        alt_path_2 = os.path.join(parent_dir, '..', 'workspace', base_name)
        if os.path.exists(os.path.join(alt_path_2, 'mesh.msh')):
            folder_path = alt_path_2
            
    mesh_file = os.path.join(folder_path, 'mesh.msh')
    stress_tensor_file = os.path.join(folder_path, 'smooth_stress_tensor.msh')
    strain_tensor_file = os.path.join(folder_path, 'smooth_strain_tensor.msh')
    force_vector_file = os.path.join(folder_path, 'force_vector.msh')

    # Strain file might be optional or new, but user asked for it. 
    # We will return it if it exists, or handle it in process_file.
    # For now, let's assume if the basic ones exist, we return what we have.
    
    if os.path.exists(mesh_file) and os.path.exists(stress_tensor_file) and os.path.exists(force_vector_file):
        return mesh_file, stress_tensor_file, force_vector_file, strain_tensor_file
    else:
        print(f"Error: MSH files not found in the {folder_path} folder.")
        print(f"Checked path: {folder_path}")
        print("Exiting.")
        sys.exit(1)
        

def process_file(selected_file, export_von_mises, export_smooth_stress, export_vtk, cleanup=True, workspace_hint=None):
    gmsh.initialize()

    folder_path = os.path.splitext(selected_file)[0]
    mesh_file, stress_tensor_file, force_vector_file, strain_tensor_file = find_msh_files(selected_file, workspace_hint)
    folder_path = os.path.dirname(mesh_file) # Update folder path to where files actually are

    print(f"\nUsing the MSH files in the {os.path.basename(folder_path)} folder:")
    print(f" - mesh.msh: {mesh_file}")
    print(f" - smooth_stress_tensor.msh: {stress_tensor_file}")
    print(f" - force_vector.msh: {force_vector_file}")
    if strain_tensor_file and os.path.exists(strain_tensor_file):
        print(f" - smooth_strain_tensor.msh: {strain_tensor_file}")

    gmsh.merge(mesh_file)
    gmsh.merge(stress_tensor_file)
    gmsh.merge(force_vector_file)
    
    # Load strain tensor if available (this will likely be view 3)
    has_strain = False
    if strain_tensor_file and os.path.exists(strain_tensor_file):
        gmsh.merge(strain_tensor_file)
        has_strain = True

    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    nodeCoords = np.array(nodeCoords).reshape((-1, 3))
    nodeData = pd.DataFrame({'NodeTag': nodeTags, 'X': nodeCoords[:, 0], 'Y': nodeCoords[:, 1], 'Z': nodeCoords[:, 2]})

    # Process Stress (View 0 or Tag 1?)
    # gmsh.view.getModelData(tag, timestep)
    # Tags usually start at 0 or 1 depending on version, but previous code used 1.
    # We should probably robustly find tags.
    # But sticking to previous logic: View 1 is Stress.
    dataType, tags, data, time, numComp = gmsh.view.getModelData(1, 0)
    svms = []
    for sig in data:
        [xx, xy, xz, yx, yy, yz, zx, zy, zz] = sig
        svm = np.sqrt(((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2 + 3 * (xy * xy + yz * yz + zx * zx))
        svms.append(svm)
    svms = np.array(svms)
    svmData = pd.DataFrame({'Von mises Stress': svms}, index=nodeTags)

    nodeData.reset_index(drop=True, inplace=True)
    svmData.reset_index(drop=True, inplace=True)
    combinedData = pd.concat([nodeData, svmData], axis=1)

    # Process Force (View 2)
    dataType_force, tags_force, data_force, time_force, numComp_force = gmsh.view.getModelData(2, 0)
    forces = []
    for force in data_force:
        [fx, fy, fz] = force
        forces.append([fx, fy, fz])
    forces = np.array(forces)
    combinedData = pd.concat([combinedData, pd.DataFrame(forces, columns=['Fx', 'Fy', 'Fz'])], axis=1)
    
    # Process Strain: support scalar nodal fields (example script) and tensor fields
    # Prefer getHomogeneousModelData when available; align data by tags
    # Prepare default equivalent_strains (zeros) so it's always defined
    equivalent_strains = np.zeros(len(nodeTags))
    if has_strain:
        try:
            view_tags = gmsh.view.getTags()
            strain_view_tag = view_tags[-1]

            # try homogeneous getter first (returns nice numpy arrays), fallback to getModelData
            try:
                dataType_strain, tags_strain, data_strain, time_strain, numComp_strain = gmsh.view.getHomogeneousModelData(strain_view_tag, 0)
                # If homogeneous and multiple components, data is flat. Reshape it.
                if numComp_strain > 1 and len(data_strain) == len(tags_strain) * numComp_strain:
                     data_strain = np.array(data_strain).reshape((len(tags_strain), numComp_strain))
            except Exception:
                dataType_strain, tags_strain, data_strain, time_strain, numComp_strain = gmsh.view.getModelData(strain_view_tag, 0)

            # robustly detect scalar field: numComp==1
            is_scalar_field = (numComp_strain == 1)

            if is_scalar_field:
                # normalize scalar list
                scalars = np.array([float(d) if np.isscalar(d) else float(d[0]) for d in data_strain])
                strain_df = pd.DataFrame({'strain_scalar': scalars}, index=tags_strain)
                strain_df = strain_df.reindex(nodeTags).reset_index(drop=True)
                combinedData = pd.concat([combinedData, strain_df], axis=1)
                equivalent_strains = strain_df['strain_scalar'].to_numpy()
            else:
                # Treat as tensor-like data (6 or 9 components) and compute principal strains
                e1s = []
                e2s = []
                e3s = []
                eqs = []
                for s in data_strain:
                    # if s is a scalar-like (defensive), treat as zeros
                    if np.isscalar(s):
                        mat = np.zeros((3, 3))
                    else:
                        # support both 9-component and 6-component representations
                        try:
                            if len(s) == 9:
                                xx, xy, xz, yx, yy, yz, zx, zy, zz = s
                                xy_s = 0.5 * (xy + yx)
                                xz_s = 0.5 * (xz + zx)
                                yz_s = 0.5 * (yz + zy)
                                mat = np.array([[xx, xy_s, xz_s], [xy_s, yy, yz_s], [xz_s, yz_s, zz]])
                            elif len(s) == 6:
                                # expected: [xx, yy, zz, xy, yz, zx]
                                xx, yy, zz, xy, yz, zx = s
                                mat = np.array([[xx, xy, zx], [xy, yy, yz], [zx, yz, zz]])
                            elif len(s) == 3:
                                vals = np.array(sorted(s))
                                e1s.append(vals[0]); e2s.append(vals[1]); e3s.append(vals[2])
                                sum_diffs = (vals[0]-vals[1])**2 + (vals[1]-vals[2])**2 + (vals[2]-vals[0])**2
                                eq = (np.sqrt(2.0)/3.0) * np.sqrt(sum_diffs)
                                eqs.append(eq)
                                continue
                            else:
                                mat = np.zeros((3, 3))
                        except Exception:
                            mat = np.zeros((3, 3))

                    vals = np.linalg.eigh(mat)[0]
                    vals = np.sort(np.real(vals))
                    e1s.append(vals[0]); e2s.append(vals[1]); e3s.append(vals[2])

                    # equivalent strain (von Mises-like) from principal strains using correct factor
                    sum_diffs = (vals[0]-vals[1])**2 + (vals[1]-vals[2])**2 + (vals[2]-vals[0])**2
                    eq = (np.sqrt(2.0)/3.0) * np.sqrt(sum_diffs)
                    eqs.append(eq)

                e1s = np.array(e1s); e2s = np.array(e2s); e3s = np.array(e3s); eqs = np.array(eqs)

                # When processing tensor data, the length should match the number of nodes
                # Create DataFrame without index first, then ensure it matches nodeTags length
                if len(e1s) == len(nodeTags):
                    strain_df = pd.DataFrame({
                        'strain_e1': e1s, 
                        'strain_e2': e2s, 
                        'strain_e3': e3s, 
                        'Equivalent Strain': eqs
                    })
                    combinedData = pd.concat([combinedData, strain_df], axis=1)
                    equivalent_strains = eqs
                else:
                    print(f"Warning: Strain data length ({len(e1s)}) doesn't match node count ({len(nodeTags)}). Using zeros.")
                    equivalent_strains = np.zeros(len(nodeTags))
        except Exception as e:
            print(f"Error processing strain data: {e}")
            equivalent_strains = np.zeros(len(nodeTags))

    output_folder = folder_path

    if export_smooth_stress:
        combinedData.to_csv(os.path.join(output_folder, 'smooth_stress_tensor.csv'), index=False)
        if has_strain:
             pass

    if export_vtk:
        points = nodeCoords.reshape(-1, 3)
        elementTypes, elementTags, nodeTagsPerElement = gmsh.model.mesh.getElements()
        cells = []
        for elementType, nodeTags in zip(elementTypes, nodeTagsPerElement):
            numNodesPerElement = gmsh.model.mesh.getElementProperties(elementType)[3]
            for element in nodeTags.reshape(-1, numNodesPerElement):
                cells.append(np.insert(element - 1, 0, numNodesPerElement))
        cellsArray = np.concatenate(cells).astype(np.int_)
        mesh = pv.PolyData(points, cellsArray)
        mesh.point_data['Von mises Stress'] = svms
        mesh.point_data['Forces'] = forces
        if has_strain:
            mesh.point_data['Equivalent Strain'] = equivalent_strains
        vtk_file_path = os.path.join(output_folder, 'combined_data.vtk')
        mesh.save(vtk_file_path)
    
    gmsh.finalize()

    if export_von_mises:
        tolerance = 1e-4
        results_list = []
        max_von_mises_stress = combinedData['Von mises Stress'].max()
        max_von_mises_stress_row = combinedData.loc[combinedData['Von mises Stress'].idxmax()]
        max_von_mises_stress_coords = max_von_mises_stress_row[['X', 'Y', 'Z']].values
        min_von_mises_stress = combinedData['Von mises Stress'].min()
        average_von_mises_stress = combinedData['Von mises Stress'].mean()
        results_list.append({
            'Value': 'Maximum',
            'Von mises Stress': max_von_mises_stress,
            'Coordinate X': max_von_mises_stress_coords[0],
            'Coordinate Y': max_von_mises_stress_coords[1],
            'Coordinate Z': max_von_mises_stress_coords[2]
        })
        results_list.append({'Value': 'Minimum', 'Von mises Stress': min_von_mises_stress})
        results_list.append({'Value': 'Average', 'Von mises Stress': average_von_mises_stress})

        combinedData2 = combinedData.sort_values(by='Von mises Stress', ascending=False)
        num_nodes = len(combinedData2)
        num_nodes_to_exclude = int(num_nodes * 0.02)
        combinedData2 = combinedData2.iloc[num_nodes_to_exclude:]
        average_von_mises_stress2 = combinedData2['Von mises Stress'].mean()
        results_list.append({'Value': 'Average (excluding 2% highest)', 'Von mises Stress': average_von_mises_stress2})

        found_areas_of_interest = False
        area_von_mises_stress = {}
        with open(selected_file, 'r', encoding='utf-8') as f:
            for line in f:
                if found_areas_of_interest and line.startswith("#"):
                    try:
                        name, coordinates_str = line.strip("#").strip().split(":")
                        coordinates_list = json.loads(coordinates_str)
                        von_mises_stresses = []
                        for coord_group in coordinates_list:
                            coordinates = [float(str(coord).strip()) for coord in coord_group]
                            x, y, z = coordinates
                            matching_rows = combinedData[
                                (abs(combinedData['X'] - x) < tolerance) &
                                (abs(combinedData['Y'] - y) < tolerance) &
                                (abs(combinedData['Z'] - z) < tolerance)
                            ]
                            if not matching_rows.empty:
                                von_mises_stress = matching_rows['Von mises Stress'].mean()
                                von_mises_stresses.append(von_mises_stress)
                            else:
                                print(f"Coordinates ({x}, {y}, {z}) not found in combinedData.")
                        if von_mises_stresses:
                            area_von_mises_stress[name.strip()] = (np.mean(von_mises_stresses), len(von_mises_stresses))
                    except Exception as e:
                        print(f"Error processing coordinates: {e}")
                elif "# Areas of interest" in line:
                    found_areas_of_interest = True
        for name, data in area_von_mises_stress.items():
            average_von_mises_stress, num_elements = data
            results_list.append({
                'Value': name,
                'Von mises Stress': average_von_mises_stress,
                'Coordinate X': None,
                'Coordinate Y': None,
                'Coordinate Z': None,
                'Number of nodes': num_elements
            })

        fixations_found = False
        accumulating = False
        json_string = ""
        with open(selected_file, 'r', encoding='utf-8') as f:
            accumulating = False
            json_string = ''
            previous_line = ''
            for line in f:
                if 'p[' in line and 'fixations' in line:
                    accumulating = True
                    json_string = '{"fixations":' + line.split('fixations')[1].split('] = ')[1].strip()
                elif accumulating:
                    if line.strip().startswith('p') and previous_line.strip().endswith(']'):
                        json_string += previous_line.strip() + "}"
                        json_string = json_string[:-3] + "]}"

                        accumulating = False
                        try:
                            fixations = json.loads(json_string.replace("'", '"'))
                            fixations_found = True
                            for fixation in fixations['fixations']:
                                x, y, z = fixation['nodes'][0]
                                matching_rows = combinedData[
                                    (abs(combinedData['X'] - x) < tolerance) &
                                    (abs(combinedData['Y'] - y) < tolerance) &
                                    (abs(combinedData['Z'] - z) < tolerance)
                                ]
                                if not matching_rows.empty():
                                    row = matching_rows.iloc[0]
                                    fx, fy, fz = row[['Fx', 'Fy', 'Fz']].values
                                    fixation['forces'] = [fx, fy, fz]
                                    results_list.append({
                                        'Value': fixation['name'],
                                        'Von mises Stress': None,
                                        'Coordinate X': x,
                                        'Coordinate Y': y,
                                        'Coordinate Z': z,
                                        'Fx': fx,
                                        'Fy': fy,
                                        'Fz': fz
                                    })
                                else:
                                    print(f"Node ({x}, {y}, {z}) not found in combinedData.")
                        except json.JSONDecodeError as e:
                            print("Error decoding JSON from accumulated string: Fixations not found. Be sure you are using python files for Fossils v1.3")
                        json_string = ""
                    else:
                        json_string += line.strip()
                        previous_line = line
        if not fixations_found:
            print("No fixations found")
        results_df = pd.DataFrame(results_list)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        print("Results:")
        print(results_df)
        results_df.to_csv(os.path.join(output_folder, 'von_mises_stress_results.csv'), index=False)
        print(f"Results saved to {os.path.join(output_folder, 'von_mises_stress_results.csv')}")

    # Cleanup: Delete everything except .vtk, .txt, and .csv (optional)
    if cleanup:
        try:
            print(f"Cleaning up folder: {output_folder}")
            for filename in os.listdir(output_folder):
                file_path = os.path.join(output_folder, filename)
                if os.path.isfile(file_path):
                    # Keep .vtk, .txt, and .csv files
                    if filename.lower().endswith(('.vtk', '.txt', '.csv')):
                        continue
                    
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {filename}")
                    except Exception as e:
                        print(f"Failed to delete {filename}: {e}")
        except Exception as e:
            print(f"Error during folder cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process Python files and convert MSH to CSV and VTK.")
    parser.add_argument("directory", help="Directory containing the Python files.")
    parser.add_argument("files", nargs='+', help="List of Python files to process.")
    parser.add_argument("--export-von-mises", action='store_true', help="Export Von mises stress results.")
    parser.add_argument("--export-smooth-stress", action='store_true', help="Export smooth stress tensor to CSV.")
    parser.add_argument("--export-vtk", action='store_true', help="Export combined data to VTK.")
    parser.add_argument("--auto-convert-results", action='store_true', help="Alias: auto convert results to VTK (same as --export-vtk)")
    parser.add_argument("--no-cleanup", action='store_true', help="Do not delete generated files after processing")
    parser.add_argument("--workspace-dir", help="Explicit path to the workspace directory containing MSH files")
    args = parser.parse_args()

    selected_files = [os.path.join(args.directory, file) for file in args.files]
    export_von_mises = args.export_von_mises
    export_smooth_stress = args.export_smooth_stress
    # auto-convert flag is an alias for export-vtk
    export_vtk = args.export_vtk or args.auto_convert_results
    cleanup = not args.no_cleanup
    workspace_dir = args.workspace_dir

    for selected_file in selected_files:
        process_file(selected_file, export_von_mises, export_smooth_stress, export_vtk, cleanup=cleanup, workspace_hint=workspace_dir)

if __name__ == "__main__":
    main()