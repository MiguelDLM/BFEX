import os
import sys

def update_opt_file(opt_file):
    try:
        with open(opt_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {opt_file} was not found.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    new_lines = []
    current_view = None

    existing_lines = set()  # Store existing lines to avoid duplicates

    for line in lines:
        # Check if we are inside a view
        if line.startswith('View['):
            current_view = line.split('[')[1].split(']')[0]

        if current_view is not None and 'ShowElement = 1;' in line:
            # Replace .ShowElement = 1; with .ShowElement = 0;
            line = line.replace('ShowElement = 1;', 'ShowElement = 0;')

        if current_view is not None and 'IntervalsType = 3;' in line:
            # Replace .IntervalsType = 3; with .IntervalsType = 2;
            line = line.replace('IntervalsType = 3;', 'IntervalsType = 2;')

        if current_view is not None and 'FileName' in line and 'Name' in line:
            # Add lines only if they don't exist
            new_lines_to_add = [
                f'View[{current_view}].DrawHexahedra = 0;\n',
                f'View[{current_view}].DrawLines = 0;\n',
                f'View[{current_view}].DrawPoints = 0;\n',
                f'View[{current_view}].DrawPrisms = 0;\n',
                f'View[{current_view}].DrawPyramids = 0;\n',
                f'View[{current_view}].DrawTrihedra = 0;\n',
                f'View[{current_view}].DrawScalars = 0;\n',
                f'View[{current_view}].DrawTensors = 1;\n',
                f'View[{current_view}].DrawTriangles = 0;\n',
                f'View[{current_view}].DrawVectors = 0;\n',
                f'View[{current_view}].RangeType = 2;\n',
                f'View[{current_view}].SaturateValues = 1;\n',
            ]

            for new_line in new_lines_to_add:
                if new_line not in existing_lines:
                    new_lines.append(new_line)
                    existing_lines.add(new_line)

        new_lines.append(line)

    try:
        with open(opt_file, 'w') as f:
            f.writelines(new_lines)
        print(f"The file {opt_file} has been successfully updated.")
        return True
    except Exception as e:
        print(f"Error writing to the file {opt_file}: {e}")
        return False

def remove_duplicates(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    unique_lines = set()
    new_lines = []

    for line in lines:
        if line not in unique_lines:
            unique_lines.add(line)
            new_lines.append(line)

    try:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Duplicates removed from {file_path}.")
        return True
    except Exception as e:
        print(f"Error writing to the file {file_path}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_opt_file.py file.opt")
    else:
        opt_file = sys.argv[1]
        success = update_opt_file(opt_file)

        if success:
            print(f"{opt_file} modified successfully.")
            input("Press ENTER to close this window.")

        # Remove duplicates after modification
        remove_duplicates(opt_file)
