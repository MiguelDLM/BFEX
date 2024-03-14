try:
    import os
    import numpy as np
    import pandas as pd
    import gmsh
    import json
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

    if os.path.exists(mesh_file) and os.path.exists(stress_tensor_file):
        return mesh_file, stress_tensor_file
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
            mesh_file, stress_tensor_file = find_msh_files(folder_path, selected_file)

            print(f"\nUsing the MSH files in the {os.path.basename(folder_path)} folder:")
            print(f" - mesh.msh: {mesh_file}")
            print(f" - smooth_stress_tensor.msh: {stress_tensor_file}")

            gmsh.merge(mesh_file)
            gmsh.merge(stress_tensor_file)

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

            combinedData.to_csv(os.path.join(folder_path, 'smooth_stress_tensor.csv'), index=False)

            gmsh.finalize()

            with open(selected_file, 'r') as f:
               for line in f:
                   if 'p[' in line and 'contact_pts' in line:
                       contact_points_str = line.split('=')[1]
                       contact_points = eval(contact_points_str)

            tolerance = 1e-4

            contact_points = []
            axis_points = []

            with open(selected_file, 'r') as f:
                for line in f:
                    if 'p[' in line and 'contact_pts' in line:
                        contact_points_str = line.split('=')[1]
                        contact_points = eval(contact_points_str)
                    elif 'p[' in line and 'axis_pt' in line:
                        axis_point_str = line.split('=')[1]
                        axis_point = eval(axis_point_str)
                        axis_points.append(axis_point)

            for point in contact_points:
                x, y, z = point
                matching_rows = combinedData[
                    (abs(combinedData['X'] - x) < tolerance) &
                    (abs(combinedData['Y'] - y) < tolerance) &
                    (abs(combinedData['Z'] - z) < tolerance)
                ]

                if not matching_rows.empty:
                    von_misses_stress = matching_rows['Von Misses Stress'].values[0]
                else:
                    print(f"Contact Point Coordinates: ({x}, {y}, {z}), Von Misses Stress: No close matches found")

            for point in axis_points:
                x, y, z = point
                matching_rows = combinedData[
                    (abs(combinedData['X'] - x) < tolerance) &
                    (abs(combinedData['Y'] - y) < tolerance) &
                    (abs(combinedData['Z'] - z) < tolerance)
                ]

                if not matching_rows.empty:
                    von_misses_stress = matching_rows['Von Misses Stress'].values[0]
                else:
                    print(f"Axis Point Coordinates: ({x}, {y}, {z}), Von Misses Stress: No close matches found")

            max_von_misses_stress = combinedData['Von Misses Stress'].max()
            max_von_misses_stress_row = combinedData.loc[combinedData['Von Misses Stress'].idxmax()]
            max_von_misses_stress_coords = max_von_misses_stress_row[['X', 'Y', 'Z']].values
            min_von_misses_stress = combinedData['Von Misses Stress'].min()
            average_von_misses_stress = combinedData['Von Misses Stress'].mean()

            results_list = []
            
            for i, point in enumerate(contact_points, start=1):
                x, y, z = point
                matching_rows = combinedData[
                    (abs(combinedData['X'] - x) < tolerance) &
                    (abs(combinedData['Y'] - y) < tolerance) &
                    (abs(combinedData['Z'] - z) < tolerance)
                ]

                if not matching_rows.empty:
                    von_misses_stress = matching_rows['Von Misses Stress'].values[0]
                    results_list.append({
                        'Value': f'Contact Point {i}',
                        'Von Misses Stress': von_misses_stress,
                        'Coordinate X': x,
                        'Coordinate Y': y,
                        'Coordinate Z': z
                    })
                else:
                    print(f"Contact Point {i} Coordinates: ({x}, {y}, {z}), Von Misses Stress: No close matches found")

            for i, point in enumerate(axis_points, start=1):
                x, y, z = point
                matching_rows = combinedData[
                    (abs(combinedData['X'] - x) < tolerance) &
                    (abs(combinedData['Y'] - y) < tolerance) &
                    (abs(combinedData['Z'] - z) < tolerance)
                ]

                if not matching_rows.empty:
                    von_misses_stress = matching_rows['Von Misses Stress'].values[0]
                    results_list.append({
                        'Value': f'Axis Point {i}',
                        'Von Misses Stress': von_misses_stress,
                        'Coordinate X': x,
                        'Coordinate Y': y,
                        'Coordinate Z': z
                    })
                else:
                    print(f"Axis Point {i} Coordinates: ({x}, {y}, {z}), Von Misses Stress: No close matches found")





            results_list.append({
                'Value': 'Maximum',
                'Von Misses Stress': max_von_misses_stress,
                'Coordinate X': max_von_misses_stress_coords[0],
                'Coordinate Y': max_von_misses_stress_coords[1],
                'Coordinate Z': max_von_misses_stress_coords[2]
            })
            results_list.append({'Value': 'Minimum', 'Von Misses Stress': min_von_misses_stress})
            results_list.append({'Value': 'Average', 'Von Misses Stress': average_von_misses_stress})
            
            #Aditional areas
            
            additional_coordinates = []
            found_areas_of_interest = False
            area_von_misses_stress = {}  # Diccionario para almacenar los promedios de Von Misses Stress por área

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
                                
                                area_von_misses_stress[name.strip()] = np.mean(von_misses_stresses)
                        except Exception as e:
                            print(f"Error processing coordinates: {e}")
                    elif "# Areas of interest" in line:
                        found_areas_of_interest = True
          
            for name, average_von_misses_stress in area_von_misses_stress.items():
                results_list.append({
                    'Value': name,
                    'Von Misses Stress': average_von_misses_stress,
                    'Coordinate X': None,
                    'Coordinate Y': None,
                    'Coordinate Z': None
                })

            results_df = pd.DataFrame(results_list)

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
