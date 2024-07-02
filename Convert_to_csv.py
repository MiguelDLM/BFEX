try:
    import os
    import numpy as np
    import pandas as pd
    import gmsh
    import json
    import pyvista as pv
    from pyvista import _vtk as vtk
except ImportError as e:
    print(f"Error: {e}")
    install_libraries = input("Some of the required libraries are not installed. Do you want to install them now? (y/n): ").lower()

    if install_libraries == 'y':
        # Install libraries using pip
        try:
            import sys
            os.system(f"{sys.executable} -m pip install numpy pandas gmsh")

            # Try to import libraries again after installation
            import numpy as np
            import pandas as pd
            import gmsh
            import json
        except Exception as install_error:
            print(f"Failed to install libraries. Error: {install_error}")
            input("Press Enter to close the script.")
            exit()
    else:
        input("Press Enter to close the script.")
        exit()


def find_python_files(directory, keyword_lines):
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if all(keyword in content for keyword in keyword_lines):
                        python_files.append(file_path)
    return python_files


def get_user_choice(python_files):
    print("Found the following Python files:")
    for i, file in enumerate(python_files, start=1):
        print(f"{i}. {file}")
    choice = input("Please choose the number of the file you want to continue with: ")
    try:
        choice_idx = int(choice) - 1
        return [python_files[choice_idx]]
    except (ValueError, IndexError):
        print("Invalid option. Exiting.")
        exit()


def find_msh_files(folder, python_file):
    folder_name = os.path.splitext(os.path.basename(python_file))[0]
    folder_path = os.path.join(os.path.dirname(python_file), folder_name)
    mesh_file = os.path.join(folder_path, 'mesh.msh')
    stress_tensor_file = os.path.join(folder_path, 'smooth_stress_tensor.msh')
    force_vector_file = os.path.join(folder_path, 'force_vector.msh')

    if os.path.exists(mesh_file) and os.path.exists(stress_tensor_file) and os.path.exists(force_vector_file):
        return mesh_file, stress_tensor_file, force_vector_file
    else:
        print(f"Error: MSH files not found in the {folder_name} folder. Exiting.")
        exit()


def main():
    script_directory = os.path.dirname(os.path.abspath(__file__))

    keyword_lines = ["def parms(d={})"]

    try:
        python_files = find_python_files(script_directory, keyword_lines)

        if not python_files:
            print("No Python files found that meet the criteria. Exiting.")
            return

        selected_files = get_user_choice(python_files)
        print(f"Selected files: {selected_files}")

        for selected_file in selected_files:
            gmsh.initialize()

            folder_path = os.path.join(script_directory, os.path.splitext(os.path.basename(selected_file))[0])
            mesh_file, stress_tensor_file, force_vector_file = find_msh_files(folder_path, selected_file)

            print(f"\nUsing the MSH files in the {os.path.basename(folder_path)} folder:")
            print(f" - mesh.msh: {mesh_file}")
            print(f" - smooth_stress_tensor.msh: {stress_tensor_file}")
            print(f" - force_vector.msh: {force_vector_file}")


            gmsh.merge(mesh_file)
            gmsh.merge(stress_tensor_file)
            gmsh.merge(force_vector_file)

            nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()

            nodeCoords = np.array(nodeCoords).reshape((-1, 3))

            nodeData = pd.DataFrame({'NodeTag': nodeTags, 'X': nodeCoords[:, 0], 'Y': nodeCoords[:, 1], 'Z': nodeCoords[:, 2]})

            dataType, tags, data, time, numComp = gmsh.view.getModelData(1, 0)

            svms = []
            for sig in data:
                [xx, xy, xz, yx, yy, yz, zx, zy, zz] = sig
                svm = np.sqrt(((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2 + 3 * (xy * xy + yz * yz + zx * zx))
                svms.append(svm)

            svms = np.array(svms)

            svmData = pd.DataFrame({'Von Misses Stress': svms}, index=nodeTags)

            nodeData.reset_index(drop=True, inplace=True)
            svmData.reset_index(drop=True, inplace=True)
            combinedData = pd.concat([nodeData, svmData], axis=1)

            dataType_force, tags_force, data_force, time_force, numComp_force = gmsh.view.getModelData(2, 0)

            forces = []
            for force in data_force:
                [fx, fy, fz] = force
                forces.append([fx, fy, fz])

            forces = np.array(forces)

            combinedData = pd.concat([combinedData, pd.DataFrame(forces, columns=['Fx', 'Fy', 'Fz'])], axis=1)

            combinedData.to_csv(os.path.join(folder_path, 'smooth_stress_tensor.csv'), index=False)

            #Export the combined data as a VTK file
            points = nodeCoords.reshape(-1, 3)
            # Obtener elementos de la malla de GMSH
            elementTypes, elementTags, nodeTagsPerElement = gmsh.model.mesh.getElements()

            # Preparar los datos de cells para PyVista
            cells = []
            for elementType, nodeTags in zip(elementTypes, nodeTagsPerElement):
                # Obtener el número de nodos por tipo de elemento (p. ej., 3 para triángulos, 4 para tetraedros)
                numNodesPerElement = gmsh.model.mesh.getElementProperties(elementType)[3]
                for element in nodeTags.reshape(-1, numNodesPerElement):
                    # Añadir el número de nodos seguido por los índices de los nodos (ajustados por -1 para base 0)
                    cells.append(np.insert(element - 1, 0, numNodesPerElement))

            # Convertir a un array de NumPy para compatibilidad con PyVista
            cellsArray = np.concatenate(cells).astype(np.int_)

            # Crear el objeto PolyData para PyVista
            mesh = pv.PolyData(points, cellsArray)
            mesh.point_data['Von Misses Stress'] = svms
            mesh.point_data['Forces'] = forces

            # Guardar el archivo VTK
            vtk_file_path = os.path.join(folder_path, 'combined_data.vtk')
            mesh.save(vtk_file_path)
            #print(f"Datos exportados como archivo VTK en {vtk_file_path}")
            gmsh.finalize()

            tolerance = 1e-4

            results_list = []
                            
            max_von_misses_stress = combinedData['Von Misses Stress'].max()
            max_von_misses_stress_row = combinedData.loc[combinedData['Von Misses Stress'].idxmax()]
            max_von_misses_stress_coords = max_von_misses_stress_row[['X', 'Y', 'Z']].values
            min_von_misses_stress = combinedData['Von Misses Stress'].min()
            average_von_misses_stress = combinedData['Von Misses Stress'].mean()
            results_list.append({
                'Value': 'Maximum',
                'Von Misses Stress': max_von_misses_stress,
                'Coordinate X': max_von_misses_stress_coords[0],
                'Coordinate Y': max_von_misses_stress_coords[1],
                'Coordinate Z': max_von_misses_stress_coords[2]
            })
            results_list.append({'Value': 'Minimum', 'Von Misses Stress': min_von_misses_stress})
            results_list.append({'Value': 'Average', 'Von Misses Stress': average_von_misses_stress})

            #extract the average von misses stress of all the nodes except the 2% of the nodes with the highest von misses stress
            combinedData2 = combinedData.sort_values(by='Von Misses Stress', ascending=False)
            num_nodes = len(combinedData2)
            num_nodes_to_exclude = int(num_nodes * 0.02)
            combinedData2 = combinedData2.iloc[num_nodes_to_exclude:]
            average_von_misses_stress2 = combinedData2['Von Misses Stress'].mean()
            results_list.append({'Value': 'Average (excluding 2% highest)', 'Von Misses Stress': average_von_misses_stress2})

            #Aditional areas
            
            found_areas_of_interest = False
            area_von_misses_stress = {}  

            with open(selected_file, 'r') as f:
                for line in f:
                    if found_areas_of_interest and line.startswith("#"):
                        try:
                            name, coordinates_str = line.strip("#").strip().split(":")
                            coordinates_list = json.loads(coordinates_str)
                            von_misses_stresses = []
                            for coord_group in coordinates_list:
                                coordinates = [float(str(coord).strip()) for coord in coord_group]
                               
                                x, y, z = coordinates
                                matching_rows = combinedData[
                                    (abs(combinedData['X'] - x) < tolerance) &
                                    (abs(combinedData['Y'] - y) < tolerance) &
                                    (abs(combinedData['Z'] - z) < tolerance)
                                ]
                                if not matching_rows.empty:
                                    von_misses_stress = matching_rows['Von Misses Stress'].mean()
                                    von_misses_stresses.append(von_misses_stress)
                                else:
                                    print(f"Coordinates ({x}, {y}, {z}) not found in combinedData.")
                            if von_misses_stresses:
                                
                                area_von_misses_stress[name.strip()] = (np.mean(von_misses_stresses), len(von_misses_stresses))
                        except Exception as e:
                            print(f"Error processing coordinates: {e}")
                    elif "# Areas of interest" in line:
                        found_areas_of_interest = True
          
            for name, data in area_von_misses_stress.items():
                average_von_misses_stress, num_elements = data
                results_list.append({
                    'Value': name,
                    'Von Misses Stress': average_von_misses_stress,
                    'Coordinate X': None,
                    'Coordinate Y': None,
                    'Coordinate Z': None,
                    'Number of nodes': num_elements
                })
            #Extract the reaction forces at the fixations 

            fixations_found = False
            accumulating = False
            json_string = ""
            with open(selected_file, 'r') as f:
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
                                    if not matching_rows.empty:
                                        row = matching_rows.iloc[0]
                                        fx, fy, fz = row[['Fx', 'Fy', 'Fz']].values
                                        fixation['forces'] = [fx, fy, fz]
                                        results_list.append({
                                            'Value': fixation['name'],
                                            'Von Misses Stress': None,
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
                                print("Error decoding JSON from accumulated string:", json_string)
                                print("JSONDecodeError:", e)

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

            results_df.to_csv(os.path.join(folder_path, 'von_misses_stress_results.csv'), index=False)
            input("Press Enter to close this window.")

    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to close the script.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to close the window.")
