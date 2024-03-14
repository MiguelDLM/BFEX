import os
import subprocess

def check_installation(package):
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_package(package):
    subprocess.call(['pip', 'install', package])

def combine_csv_files():
    # Check if pandas is installed, if not, ask the user to install
    if not check_installation('pandas'):
        user_input = input("Pandas is not installed. Would you like to install it now? (y/n): ")
        if user_input.lower() == 'y':
            install_package('pandas')
        else:
            print("Exiting the script. Please install pandas and rerun the script.")
            return

    # Check if matplotlib is installed, if not, ask the user to install
    if not check_installation('matplotlib'):
        user_input = input("Matplotlib is not installed. Would you like to install it now? (y/n): ")
        if user_input.lower() == 'y':
            install_package('matplotlib')
        else:
            print("Exiting the script. Please install matplotlib and rerun the script.")
            return

    # Import libraries after checking/installing
    import pandas as pd
    import matplotlib.pyplot as plt
    
    # Get the current path
    current_path = os.getcwd()

    # Search for von_misses_stress_results.csv files in all subfolders
    csv_files = []
    for root, dirs, files in os.walk(current_path):
        for file in files:
            if file == 'von_misses_stress_results.csv':
                csv_files.append(os.path.join(root, file))

    # Display the found files and prompt the user to choose
    print("Found files:")
    for i, file in enumerate(csv_files):
        print(f"{i + 1}. {file}")

    user_choice = input("Choose files by entering the numbers separated by commas (e.g., 1, 2) or 'all' to process all: ")

    if user_choice.lower() == 'all':
        selected_files = csv_files
    else:
        selected_indices = [int(index) - 1 for index in user_choice.split(',')]
        selected_files = [csv_files[index] for index in selected_indices]

    # Combine the selected files into a DataFrame
    combined_data = pd.DataFrame()
    for file in selected_files:
        folder_name = os.path.basename(os.path.dirname(file))
        df = pd.read_csv(file, usecols=[0, 1], header=None, skiprows=1)
        df.columns = ['Value', 'Von Misses Stress']  # Renaming columns for consistency
        df.insert(0, 'Folder Name', folder_name)
        combined_data = pd.concat([combined_data, df])

    # Save the result to a new CSV file
    combined_data.to_csv('combined_results.csv', index=False)
    print("Files successfully combined. Results saved in combined_results.csv")
    
    grouped_data = combined_data.groupby(["Folder Name", "Value"])["Von Misses Stress"].mean()
    subcategories = grouped_data.index.get_level_values("Value").unique()

    # Interacción para elegir subcategorías
    print("Subcategorías disponibles:")
    for i, subcat in enumerate(subcategories):
        print(f"{i + 1}. {subcat}")

    choices = input("Select subcategories separated by commas (e.g., 1,2,3) or enter 'all' to view all subcategories: ")

    # Filtrar datos según la elección del usuario
    if choices.lower() == "all":
        selected_data = grouped_data
    else:
        selected_indices = [int(idx) - 1 for idx in choices.split(",")]
        selected_subcats = subcategories[selected_indices]
        selected_data = grouped_data[grouped_data.index.get_level_values("Value").isin(selected_subcats)]


    # Creación del gráfico
    plt.figure(figsize=(10, 6))
    line_styles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "D", "v", "P", "*", "X", "h"]
    for i, (subcat, values) in enumerate(selected_data.groupby("Value")):
        plt.plot(values.index.get_level_values("Folder Name"), values, marker=markers[i % len(markers)], label=subcat, linestyle=line_styles[i % len(line_styles)], lw =2)

    plt.xlabel("Number of faces")
    plt.ylabel("Von Misses Stress")
    plt.title("Von Misses Stress Variation")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    combine_csv_files()
    input("Press Enter to close this window")
