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
        df = pd.read_csv(file, usecols=[1], header=None, skiprows=1).T
        df.insert(0, 'Folder Name', folder_name)
        combined_data = pd.concat([combined_data, df])
        
    combined_data.columns = ['Folder Name', 'Contact Point 1', 'Axis Point 1', 'Axis Point 2', 'Maximum', 'Minimum', 'Average']
    # Save the result to a new CSV file
    combined_data.to_csv('combined_results.csv', index=False)
    print("Files successfully combined. Results saved in combined_results.csv")
    
    # Plotting the data
    plt.figure(figsize=(10, 6))
    line_styles = ['-', '--', '-.', ':']  # Definir diferentes estilos de línea

    for i, column in enumerate(combined_data.columns[1:]):
        plt.plot(combined_data['Folder Name'], combined_data[column], label=column, linestyle=line_styles[i % len(line_styles)])

    plt.xlabel('Number of faces')
    plt.ylabel('Von Misses Stress')
    plt.title('Sensitivity Analysis results')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  
    plt.tight_layout()  
    plt.savefig('comparison_plot.png')
    print("Comparison plot successfully saved as comparison_plot.png")

    # Show the plot
    plt.show()
if __name__ == "__main__":
    combine_csv_files()
    input("Press Enter to close this window")
