import os
import platform

def contiene_def_parms(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines[:12]:
            if 'def parms(d={}):' in line or 'import os' in line or 'path = os.path.join' in line:
                return True
    return False

def find_python_files(path):
    python_files = []
    for current_folder, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(current_folder, file)
            if file.endswith(".py") and not file == os.path.basename(__file__) and contiene_def_parms(file_path):
                python_files.append(file_path)
    return python_files

def show_file_list(files):
    print("Python files found:")
    for i, file in enumerate(files, start=1):
        print(f"{i}. {file}")
    print("0. All")

def execute_program(file):
    if platform.system() == "Windows":
        program_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Fossils", "fossils.exe")
        os.startfile(program_path, 'open', f'"{file}" --nogui')
    elif platform.system() == "Linux":
        wine_command = "wine" if os.path.isfile("/usr/bin/wine") else "wine64"
        wine_path = os.path.expanduser("~/.wine/drive_c/Program Files (x86)/Fossils/fossils.exe")
        os.system(f"{wine_command} '{wine_path}' '{file}' --nogui")

def execute_all(files):
    for file in files:
        execute_program(file)

def main():
    current_folder = os.getcwd()
    python_files = find_python_files(current_folder)

    if not python_files:
        print("No Python files found.")
        return

    show_file_list(python_files)

    selection = input("Select the number of the file you want to execute (or 'all'): ")

    if selection.lower() == "all":
        execute_all(python_files)
    else:
        selected_files = [int(x.strip()) for x in selection.split(',') if x.strip().isdigit()]
        for selected_file in selected_files:
            if 0 < selected_file <= len(python_files):
                file_selected = python_files[selected_file - 1]
                execute_program(file_selected)
            else:
                print(f"Selection {selected_file} is not valid.")

if __name__ == "__main__":
    main()
