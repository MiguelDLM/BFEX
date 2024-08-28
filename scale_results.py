import os
import pandas as pd
import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

def find_vtk_files(directory):
    vtk_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.vtk'):
                vtk_files.append(os.path.join(root, file))
    return vtk_files

def get_user_choice(vtk_files):
    print("\nList of .vtk files in the directory:")
    for i, vtk_file in enumerate(vtk_files):
        print(f"{i+1}. {vtk_file}")

    selected_option = input("Enter the indices of files to use (comma-separated) or 'all' to use all: ")
    if selected_option.lower() == 'all':
        return vtk_files
    else:
        selected_indices = selected_option.split(',')
        selected_files = [vtk_files[int(index)-1] for index in selected_indices]
        return selected_files

def get_variable_choice(array_names):
    print("\nList of variables in the file:")
    for i, name in enumerate(array_names):
        print(f"{i+1}. {name}")

    selected_option = input("Enter the index of the variable to modify: ")
    selected_variable = array_names[int(selected_option) - 1]
    return selected_variable

def read_vtk_to_dataframe(vtk_file):
    reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(vtk_file)
    reader.Update()
    
    data = reader.GetOutput()
    point_data = data.GetPointData()
    array_names = [point_data.GetArrayName(i) for i in range(point_data.GetNumberOfArrays())]
    
    data_dict = {}
    for name in array_names:
        vtk_array = point_data.GetArray(name)
        np_array = vtk_to_numpy(vtk_array)
        
        # Check if the array is multidimensional
        if np_array.ndim > 1:
            for dim in range(np_array.shape[1]):
                data_dict[f"{name}_{dim}"] = np_array[:, dim]
        else:
            data_dict[name] = np_array
    
    df = pd.DataFrame(data_dict)
    return df, data, array_names

def save_scaled_vtk(df, data, vtk_file, variable_name):
    point_data = data.GetPointData()
    vtk_array = point_data.GetArray(variable_name)
    np_array = df[variable_name].to_numpy()
    scaled_vtk_array = numpy_to_vtk(np_array)
    scaled_vtk_array.SetName(variable_name)
    point_data.RemoveArray(variable_name)
    point_data.AddArray(scaled_vtk_array)
    
    writer = vtk.vtkGenericDataObjectWriter()
    new_file_name = vtk_file.replace('.vtk', '.vtk')
    writer.SetFileName(new_file_name)
    writer.SetInputData(data)
    writer.Write()
    print(f"Scaled file saved as {new_file_name}")

def main():
    directory = os.path.dirname(os.path.abspath(__file__))
    vtk_files = find_vtk_files(directory)
    
    if not vtk_files:
        print("No .vtk files found in the directory.")
        return
    
    selected_files = get_user_choice(vtk_files)
    print("\nSelected .vtk files:")
    for file in selected_files:
        print(file)
    
    # Read the first file to get the list of variables
    df, data, array_names = read_vtk_to_dataframe(selected_files[0])
    selected_variable = get_variable_choice(array_names)
    scale_factor = float(input(f"Enter the scale factor for {selected_variable}: "))
    
    for file in selected_files:
        df, data, _ = read_vtk_to_dataframe(file)
        df[selected_variable] *= scale_factor
        save_scaled_vtk(df, data, file, selected_variable)

if __name__ == "__main__":
    main()