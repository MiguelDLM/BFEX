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

    combined_data = pd.DataFrame()
    for file in selected_files:
        folder_name = os.path.basename(os.path.dirname(file))
        df = pd.read_csv(file, usecols=[0, 1, 6, 7, 8], header=None, skiprows=1)
        df.columns = ['Value', 'Von Misses Stress', 'Fx', 'Fy', 'Fz']
        df.insert(0, 'Folder Name', folder_name)
        df = df.sort_values(by=['Folder Name', 'Value'])
        combined_data = pd.concat([combined_data, df])


    combined_data = combined_data.sort_values(by=['Folder Name', 'Value'])
    #remove the subfix of the folder name _faces
    combined_data['Folder Name'] = combined_data['Folder Name'].str.replace('_faces', '')
    missing_vms = combined_data['Von Misses Stress'].isnull()
    if missing_vms.any():
        print("Some selected subcategories do not have data in 'Von Misses Stress'.")

        column_map = {'1': 'Fx', '2': 'Fy', '3': 'Fz', 'fx': 'Fx', 'fy': 'Fy', 'fz': 'Fz'}

        while True:
            alternative_column_input = input("Please select an alternative column (1: Fx, 2: Fy, 3: Fz): ").lower()

            alternative_column = column_map.get(alternative_column_input)
            if alternative_column:

                break
            else:
                print("Invalid selection. Please choose between 1: Fx, 2: Fy, 3: Fz.")


        df_alternative = combined_data.loc[missing_vms, ['Folder Name', 'Value', alternative_column]].copy()


    grouped_data = combined_data.groupby(["Folder Name", "Value"])["Von Misses Stress"].mean()
    subcategories = grouped_data.index.get_level_values("Value").unique()


    print("Available subcategories:")
    for i, subcat in enumerate(subcategories):
        print(f"{i + 1}. {subcat}")

    choices = input("Select subcategories by number, use '-' to exclude (e.g., 1,2,-3) or 'all except' followed by numbers to exclude (e.g., all except 3,4): ")

    if choices.lower().startswith("all except"):
        exclude_indices = [int(idx) - 1 for idx in choices.replace("all except", "").split(",")]
        selected_subcats = [subcat for i, subcat in enumerate(subcategories) if i not in exclude_indices]
    elif choices.lower() == "all":
        selected_subcats = subcategories
    else:
        selected_indices = []
        exclude_indices = []
        for choice in choices.split(","):
            if choice.startswith("-"):
                exclude_indices.append(int(choice[1:]) - 1)
            else:
                selected_indices.append(int(choice) - 1)
        
        if exclude_indices:
            selected_subcats = [subcat for i, subcat in enumerate(subcategories) if i not in exclude_indices]
        else:
            selected_subcats = [subcategories[i] for i in selected_indices]

    selected_data = grouped_data[grouped_data.index.get_level_values("Value").isin(selected_subcats)]
    selected_data = selected_data.dropna()

    plt.figure(figsize=(10, 6))
    ax1 = plt.gca()

    markers = ["o", "s", "^", "D", "v", "P", "*", "X", "h"]
    for i, (subcat, values) in enumerate(selected_data.groupby("Value")):
        ax1.plot(values.index.get_level_values("Folder Name"), values, marker=markers[i % len(markers)], label=subcat, linestyle="-", lw=2)  

    ax1.set_xlabel("Number of faces")
    ax1.set_ylabel("Von Misses Stress")
    ax1.set_title("Forces and Stress variation across different number of faces")
    ax1.grid(False)

    ax2 = ax1.twinx()

    for i, (subcat, values) in enumerate(df_alternative.groupby("Value")):
        ax2.plot(values['Folder Name'], values[alternative_column], marker=markers[i % len(markers)], label=subcat, linestyle="--", lw=2, alpha=0.5) 

    ax2.set_ylabel(alternative_column)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    combined_handles = handles1 + handles2
    combined_labels = labels1 + labels2

    ax1.legend(combined_handles, combined_labels, loc='upper left', bbox_to_anchor=(1.05, 1))

    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    combine_csv_files()
    input("Press Enter to close this window")
