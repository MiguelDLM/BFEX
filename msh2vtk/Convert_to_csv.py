import os
import numpy as np
import pandas as pd
import gmsh
import json
import pyvista as pv
from pyvista import _vtk as vtk
import argparse
import sys
import re

def gmsh_to_vtk_type(gmsh_type):
    # Mapping Gmsh element types to VTK cell types
    mapping = {
        1: 3,   # 2-node line -> VTK_LINE
        2: 5,   # 3-node triangle -> VTK_TRIANGLE
        3: 9,   # 4-node quadrangle -> VTK_QUAD
        4: 10,  # 4-node tetrahedron -> VTK_TETRA
        5: 12,  # 8-node hexahedron -> VTK_HEXAHEDRON
        6: 13,  # 6-node prism -> VTK_WEDGE
        7: 14,  # 5-node pyramid -> VTK_PYRAMID
        15: 1,  # 1-node point -> VTK_VERTEX
    }
    return mapping.get(gmsh_type, 0)

def find_msh_folder(python_file, workspace_hint=None):
    folder_path = os.path.splitext(python_file)[0]
    
    # 1. Workspace hint
    if workspace_hint and os.path.isdir(workspace_hint):
        if os.path.exists(os.path.join(workspace_hint, 'mesh.msh')):
            return workspace_hint
            
    # 2. Default location
    if os.path.exists(os.path.join(folder_path, 'mesh.msh')):
        return folder_path
        
    # 3. Workspace subdirs
    base_name = os.path.splitext(os.path.basename(python_file))[0]
    parent_dir = os.path.dirname(python_file)
    
    alt_path = os.path.join(parent_dir, 'workspace', base_name)
    if os.path.exists(os.path.join(alt_path, 'mesh.msh')):
        return alt_path
        
    alt_path_2 = os.path.join(parent_dir, '..', 'workspace', base_name)
    if os.path.exists(os.path.join(alt_path_2, 'mesh.msh')):
        return alt_path_2
        
    return None

def process_file(selected_file, export_von_mises, export_smooth_stress, export_vtk, cleanup=True, workspace_hint=None):
    if not gmsh.isInitialized():
        gmsh.initialize()

    folder_path = find_msh_folder(selected_file, workspace_hint)
    if not folder_path:
        print(f"Error: MSH files (mesh.msh) not found for {selected_file}")
        # Only exit if strict, but let's try to be helpful
        # gmsh.finalize() # Don't finalize if we want to process next file in main loop? 
        # But here process_file is called per file.
        return

    print(f"\nProcessing results in: {folder_path}")
    output_folder = folder_path

    # Load Mesh
    mesh_file = os.path.join(folder_path, 'mesh.msh')
    try:
        gmsh.merge(mesh_file)
    except Exception as e:
        print(f"Error merging mesh: {e}")
        return

    # Load all other .msh files (Universal Integration)
    loaded_files = {os.path.abspath(mesh_file)}
    
    # Check post.opt first (priority)
    post_opt = os.path.join(folder_path, "post.opt")
    if os.path.exists(post_opt):
        try:
            with open(post_opt, 'r') as f:
                content = f.read()
                matches = re.findall(r'View\[.+\]\.FileName = "(.+)";', content)
                for m in matches:
                    fpath = os.path.join(folder_path, m) if not os.path.isabs(m) else m
                    if os.path.exists(fpath) and os.path.abspath(fpath) not in loaded_files:
                        try:
                            gmsh.merge(fpath)
                            loaded_files.add(os.path.abspath(fpath))
                            print(f"Merged {os.path.basename(fpath)}")
                        except Exception as e:
                            print(f"Error merging {fpath}: {e}")
        except Exception as e:
            print(f"Error reading post.opt: {e}")

    # Scan directory for any other .msh files
    for f in os.listdir(folder_path):
        if f.endswith('.msh'):
            fpath = os.path.join(folder_path, f)
            if os.path.abspath(fpath) not in loaded_files:
                try:
                    gmsh.merge(fpath)
                    loaded_files.add(os.path.abspath(fpath))
                    print(f"Merged {f}")
                except:
                    pass

    # Extract Nodes
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    if len(nodeTags) == 0:
        print("No nodes found.")
        return

    # Create mapping for nodes
    # Check if contiguous for optimization
    min_tag = np.min(nodeTags)
    max_tag = np.max(nodeTags)
    is_contiguous = (min_tag == 1 and max_tag == len(nodeTags))
    
    if is_contiguous:
        nodes_map = None
    else:
        nodes_map = {tag: i for i, tag in enumerate(nodeTags)}
        
    points = np.array(nodeCoords).reshape(-1, 3)
    
    # Initialize combinedData for CSV exports
    nodeData = pd.DataFrame({'NodeTag': nodeTags, 'X': points[:, 0], 'Y': points[:, 1], 'Z': points[:, 2]})
    combinedData = nodeData.copy()
    
    # Prepare VTK Grid
    cells_list = []
    cell_types = []
    elem_types = gmsh.model.mesh.getElementTypes()
    
    for etype in elem_types:
        etags, enodes = gmsh.model.mesh.getElementsByType(etype)
        if len(etags) == 0: continue
        props = gmsh.model.mesh.getElementProperties(etype)
        n_nodes = props[3]
        enodes = np.array(enodes).reshape(-1, n_nodes)
        
        # Map nodes
        if is_contiguous:
            mapped_nodes = enodes - 1
        else:
            flat_enodes = enodes.flatten()
            mapped_flat = np.array([nodes_map.get(t, -1) for t in flat_enodes])
            mapped_nodes = mapped_flat.reshape(-1, n_nodes)
        
        if np.any(mapped_nodes == -1):
            continue # Skip elements with missing nodes
            
        padding = np.full((mapped_nodes.shape[0], 1), n_nodes)
        cells_chunk = np.hstack((padding, mapped_nodes)).flatten()
        cells_list.append(cells_chunk.astype(int))
        cell_types.append(np.full(len(etags), gmsh_to_vtk_type(etype)))
        
    if cells_list:
        grid = pv.UnstructuredGrid(np.concatenate(cells_list), np.concatenate(cell_types), points)
    else:
        # Fallback to points only if no elements
        grid = pv.PolyData(points)

    # Process Views
    views = gmsh.view.getTags()
    
    for vtag in views:
        try:
            vname = gmsh.view.getName(vtag)
        except:
            vname = f"View_{vtag}"
            
        clean_name = os.path.basename(vname).replace('.msh', '')
        
        # Get Data
        try:
            dataType, tags, data, time, numComp = gmsh.view.getHomogeneousModelData(vtag, 0)
        except:
            try:
                dataType, tags, data, time, numComp = gmsh.view.getModelData(vtag, 0)
            except:
                continue
                
        if len(data) == 0: continue
        
        data_arr = np.array(data)
        if len(data_arr) == len(tags) * numComp:
            data_arr = data_arr.reshape(-1, numComp)
            
        if dataType == "NodeData":
            full_data = np.full((len(nodeTags), numComp), np.nan)
            
            if is_contiguous:
                indices = np.array(tags, dtype=int) - 1
                mask = (indices >= 0) & (indices < len(nodeTags))
                if np.any(mask):
                    full_data[indices[mask]] = data_arr[mask]
            else:
                valid_indices = []
                valid_data_indices = []
                for i, tag in enumerate(tags):
                    idx = nodes_map.get(tag)
                    if idx is not None:
                        valid_indices.append(idx)
                        valid_data_indices.append(i)
                if valid_indices:
                    full_data[valid_indices] = data_arr[valid_data_indices]
            
            # Add to VTK
            if numComp == 1:
                grid.point_data[clean_name] = full_data.flatten()
            else:
                grid.point_data[clean_name] = full_data
                
            # Special Handling for known types (for CSV/Summary)
            # Von Mises (9 components)
            if numComp == 9:
                try:
                    xx = full_data[:, 0]; xy = full_data[:, 1]; xz = full_data[:, 2]
                    yx = full_data[:, 3]; yy = full_data[:, 4]; yz = full_data[:, 5]
                    zx = full_data[:, 6]; zy = full_data[:, 7]; zz = full_data[:, 8]
                    
                    j2 = np.sqrt( ((xx-yy)**2 + (yy-zz)**2 + (zz-xx)**2 )/2 + 3*(xy*xy+yz*yz+zx*zx) )
                    
                    grid.point_data[f"{clean_name}_VonMises"] = j2
                    
                    # Update combinedData for Summary if this looks like stress or if it's the only tensor
                    # Heuristic: if name contains 'stress'
                    if "stress" in clean_name.lower():
                         svmData = pd.DataFrame({'Von mises Stress': j2}, index=nodeTags)
                         # Combine properly (avoid duplicate columns if already exists)
                         if 'Von mises Stress' in combinedData.columns:
                             combinedData['Von mises Stress'] = j2 # Overwrite or rename?
                         else:
                             combinedData = pd.concat([combinedData, svmData], axis=1)
                         
                         if export_smooth_stress:
                             stress_cols = [f'stress_{i}' for i in range(9)]
                             stress_df = pd.DataFrame(full_data, columns=stress_cols, index=nodeTags)
                             combinedData = pd.concat([combinedData, stress_df], axis=1)

                    elif "strain" in clean_name.lower():
                         # Add strain components to VTK as scalars too (requested in original code)
                         grid.point_data['strain_xx'] = xx
                         grid.point_data['strain_yy'] = yy
                         grid.point_data['strain_zz'] = zz
                         grid.point_data['strain_xy'] = xy
                         grid.point_data['strain_xz'] = xz
                         grid.point_data['strain_yz'] = yz
                         mag = np.sqrt(xx**2 + yy**2 + zz**2 + 2*(xy**2 + yz**2 + xz**2))
                         grid.point_data['strain_magnitude'] = mag
                except: pass
                
            # Forces (3 components)
            elif numComp == 3:
                mag = np.linalg.norm(full_data, axis=1)
                grid.point_data[f"{clean_name}_Magnitude"] = mag
                
                if "force" in clean_name.lower() or "load" in clean_name.lower():
                    force_df = pd.DataFrame(full_data, columns=['Fx', 'Fy', 'Fz'], index=nodeTags)
                    if 'Fx' not in combinedData.columns:
                        combinedData = pd.concat([combinedData, force_df], axis=1)

    # Save VTK
    if export_vtk:
        vtk_path = os.path.join(output_folder, 'combined_data.vtk')
        grid.save(vtk_path)
        print(f"Saved VTK: {vtk_path}")

    # CSV Exports (using combinedData)
    combinedData = combinedData.loc[:, ~combinedData.columns.duplicated()]
    
    if export_smooth_stress:
        combinedData.to_csv(os.path.join(output_folder, 'smooth_stress_tensor.csv'), index=False)
        
    if export_von_mises and 'Von mises Stress' in combinedData.columns:
         export_von_mises_summary(selected_file, combinedData, output_folder)
         
    # We generally don't finalize in a loop if we are in the same process, 
    # but Convert_to_csv.py is called as a subprocess per file, so finalize is fine.
    gmsh.finalize()

    # Cleanup
    if cleanup:
        try:
            print(f"Cleaning up folder: {output_folder}")
            keep_exts = ('.msh', '.vtk', '.txt', '.csv', '.tsv', '.vtp', '.ply')
            for filename in os.listdir(output_folder):
                file_path = os.path.join(output_folder, filename)
                if os.path.isfile(file_path):
                    if not filename.lower().endswith(keep_exts):
                        try:
                            os.remove(file_path)
                        except: pass
        except: pass

def export_von_mises_summary(selected_file, combinedData, output_folder):
    try:
        tolerance = 1e-4
        results_list = []
        
        max_von_mises_stress = combinedData['Von mises Stress'].max()
        max_von_mises_stress_row = combinedData.loc[combinedData['Von mises Stress'].idxmax()]
        # Handle case where indices are not aligned or duplicate
        if isinstance(max_von_mises_stress_row, pd.DataFrame):
            max_von_mises_stress_row = max_von_mises_stress_row.iloc[0]
            
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
        if os.path.exists(selected_file):
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

        # Fixations
        fixations_found = False
        if os.path.exists(selected_file) and 'Fx' in combinedData.columns:
            accumulating = False
            json_string = ""
            with open(selected_file, 'r', encoding='utf-8') as f:
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
                                    if not matching_rows.empty:
                                        row = matching_rows.iloc[0]
                                        fx, fy, fz = row[['Fx', 'Fy', 'Fz']].values
                                        results_list.append({
                                            'Value': fixation['name'],
                                            'Von mises Stress': None,
                                            'Coordinate X': x, 'Coordinate Y': y, 'Coordinate Z': z,
                                            'Fx': fx, 'Fy': fy, 'Fz': fz
                                        })
                            except: pass
                            json_string = ""
                        else:
                            json_string += line.strip()
                            previous_line = line
                            
        results_df = pd.DataFrame(results_list)
        print("Results Summary:")
        print(results_df)
        results_df.to_csv(os.path.join(output_folder, 'von_mises_stress_results.csv'), index=False)

    except Exception as e:
        print(f"Error creating summary: {e}")

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
    export_vtk = args.export_vtk or args.auto_convert_results
    cleanup = not args.no_cleanup
    workspace_dir = args.workspace_dir

    for selected_file in selected_files:
        process_file(selected_file, export_von_mises, export_smooth_stress, export_vtk, cleanup=cleanup, workspace_hint=workspace_dir)

if __name__ == "__main__":
    main()
