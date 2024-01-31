import os
import sys

def update_opt_file(opt_file):
    try:
        with open(opt_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {opt_file} was not found.")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

    new_lines = []
    current_view = None

    for line in lines:
        # Check if we are inside a view
        if line.startswith('View['):
            current_view = line.split('[')[1].split(']')[0]

        new_lines.append(line)

        if current_view is not None and 'FileName' in line and 'Name' in line:
            # Add missing lines
            new_lines.append(f'View[{current_view}].DrawHexahedra = 0;\n')
            new_lines.append(f'View[{current_view}].DrawLines = 0;\n')
            new_lines.append(f'View[{current_view}].DrawPoints = 0;\n')
            new_lines.append(f'View[{current_view}].DrawPrisms = 0;\n')
            new_lines.append(f'View[{current_view}].DrawPyramids = 0;\n')
            new_lines.append(f'View[{current_view}].DrawTrihedra = 0;\n')
            new_lines.append(f'View[{current_view}].DrawScalars = 0;\n')
            new_lines.append(f'View[{current_view}].DrawTensors = 1;\n')
            new_lines.append(f'View[{current_view}].DrawTriangles = 0;\n')
            new_lines.append(f'View[{current_view}].DrawVectors = 0;\n')
            new_lines.append(f'View[{current_view}].RangeType = 2;\n')
            new_lines.append(f'View[{current_view}].SaturateValues = 1;\n')

    try:
        with open(opt_file, 'w') as f:
            f.writelines(new_lines)
        print(f"The file {opt_file} has been successfully updated.")
    except Exception as e:
        print(f"Error writing to the file {opt_file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_opt_file.py file.opt")
    else:
        opt_file = sys.argv[1]
        update_opt_file(opt_file)
