import os
import sys
import re

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
    existing_lines = set() 
    current_view_lines = [] 
    current_view = None

    existing_lines = set()  # Store existing lines to avoid duplicates

    for line in lines:
        # Check if we are inside a view
        if line.startswith('View['):
            if current_view is not None:
                # Agregar líneas específicas de la vista actual a new_lines
                new_lines.extend(current_view_lines)
                existing_lines.update(current_view_lines)
                current_view_lines = []  # Restablecer para la nueva vista

            current_view = line.split('[')[1].split(']')[0]

        if current_view is not None and 'ShowElement = 1;' in line:
            # Replace .ShowElement = 1; with .ShowElement = 0;
            line = line.replace('ShowElement = 1;', 'ShowElement = 0;')

        if current_view is not None and 'IntervalsType = 3;' in line:
            # Replace .IntervalsType = 3; with .IntervalsType = 2;
            line = line.replace('IntervalsType = 3;', 'IntervalsType = 2;')

        if current_view is not None:
            # Agregar líneas específicas de la vista actual a current_view_lines
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
                f'View[{current_view}].ColorTable = {{'
                f""" {{68, 1, 84, 255}}, {{68, 2, 85, 255}}, {{68, 3, 87, 255}}, {{69, 5, 88, 255}},"""				
                f""" {{69, 6, 90, 255}}, {{69, 8, 91, 255}}, {{70, 9, 92, 255}}, {{70, 11, 94, 255}},"""				
                f"""{{70, 12, 95, 255}}, {{70, 14, 97, 255}}, {{71, 15, 98, 255}}, {{71, 17, 99, 255}},"""				
                f"""{{71, 18, 101, 255}}, {{71, 20, 102, 255}}, {{71, 21, 103, 255}}, {{71, 22, 105, 255}},"""				
                f"""{{71, 24, 106, 255}}, {{72, 25, 107, 255}}, {{72, 26, 108, 255}}, {{72, 28, 110, 255}},"""				
                f"""{{72, 29, 111, 255}}, {{72, 30, 112, 255}}, {{72, 32, 113, 255}}, {{72, 33, 114, 255}},"""				
                f"""{{72, 34, 115, 255}}, {{72, 35, 116, 255}}, {{71, 37, 117, 255}}, {{71, 38, 118, 255}},"""				
                f"""{{71, 39, 119, 255}}, {{71, 40, 120, 255}}, {{71, 42, 121, 255}}, {{71, 43, 122, 255}},"""				
                f"""{{71, 44, 123, 255}}, {{70, 45, 124, 255}}, {{70, 47, 124, 255}}, {{70, 48, 125, 255}},"""			
                f"""{{70, 49, 126, 255}}, {{69, 50, 127, 255}}, {{69, 52, 127, 255}}, {{69, 53, 128, 255}},"""				
                f"""{{69, 54, 129, 255}}, {{68, 55, 129, 255}}, {{68, 57, 130, 255}}, {{67, 58, 131, 255}},"""				
                f"""{{67, 59, 131, 255}}, {{67, 60, 132, 255}}, {{66, 61, 132, 255}}, {{66, 62, 133, 255}},"""				
                f"""{{66, 64, 133, 255}}, {{65, 65, 134, 255}}, {{65, 66, 134, 255}}, {{64, 67, 135, 255}},"""				
                f"""{{64, 68, 135, 255}}, {{63, 69, 135, 255}}, {{63, 71, 136, 255}}, {{62, 72, 136, 255}},"""				
                f"""{{62, 73, 137, 255}}, {{61, 74, 137, 255}}, {{61, 75, 137, 255}}, {{61, 76, 137, 255}},"""				
                f"""{{60, 77, 138, 255}}, {{60, 78, 138, 255}}, {{59, 80, 138, 255}}, {{59, 81, 138, 255}},"""				
                f"""{{58, 82, 139, 255}}, {{58, 83, 139, 255}}, {{57, 84, 139, 255}}, {{57, 85, 139, 255}},"""				
                f"""{{56, 86, 139, 255}}, {{56, 87, 140, 255}}, {{55, 88, 140, 255}}, {{55, 89, 140, 255}},"""				
                f"""{{54, 90, 140, 255}}, {{54, 91, 140, 255}}, {{53, 92, 140, 255}}, {{53, 93, 140, 255}},"""				
                f"""{{52, 94, 141, 255}}, {{52, 95, 141, 255}}, {{51, 96, 141, 255}}, {{51, 97, 141, 255}},"""				
                f"""{{50, 98, 141, 255}}, {{50, 99, 141, 255}}, {{49, 100, 141, 255}}, {{49, 101, 141, 255}},"""				
                f"""{{49, 102, 141, 255}}, {{48, 103, 141, 255}}, {{48, 104, 141, 255}}, {{47, 105, 141, 255}},"""				
                f"""{{47, 106, 141, 255}}, {{46, 107, 142, 255}}, {{46, 108, 142, 255}}, {{46, 109, 142, 255}},"""				
                f"""{{45, 110, 142, 255}}, {{45, 111, 142, 255}}, {{44, 112, 142, 255}}, {{44, 113, 142, 255}},"""				
                f"""{{44, 114, 142, 255}}, {{43, 115, 142, 255}}, {{43, 116, 142, 255}}, {{42, 117, 142, 255}},"""				
                f"""{{42, 118, 142, 255}}, {{42, 119, 142, 255}}, {{41, 120, 142, 255}}, {{41, 121, 142, 255}},"""				
                f"""{{40, 122, 142, 255}}, {{40, 122, 142, 255}}, {{40, 123, 142, 255}}, {{39, 124, 142, 255}},"""				
                f"""{{39, 125, 142, 255}}, {{39, 126, 142, 255}}, {{38, 127, 142, 255}}, {{38, 128, 142, 255}},"""				
                f"""{{38, 129, 142, 255}}, {{37, 130, 142, 255}}, {{37, 131, 141, 255}}, {{36, 132, 141, 255}},"""				
                f"""{{36, 133, 141, 255}}, {{36, 134, 141, 255}}, {{35, 135, 141, 255}}, {{35, 136, 141, 255}},"""				
                f"""{{35, 137, 141, 255}}, {{34, 137, 141, 255}}, {{34, 138, 141, 255}}, {{34, 139, 141, 255}},"""				
                f"""{{33, 140, 141, 255}}, {{33, 141, 140, 255}}, {{33, 142, 140, 255}}, {{32, 143, 140, 255}},"""				
                f"""{{32, 144, 140, 255}}, {{32, 145, 140, 255}}, {{31, 146, 140, 255}}, {{31, 147, 139, 255}},"""				
                f"""{{31, 148, 139, 255}}, {{31, 149, 139, 255}}, {{31, 150, 139, 255}}, {{30, 151, 138, 255}},"""				
                f"""{{30, 152, 138, 255}}, {{30, 153, 138, 255}}, {{30, 153, 138, 255}}, {{30, 154, 137, 255}},"""				
                f"""{{30, 155, 137, 255}}, {{30, 156, 137, 255}}, {{30, 157, 136, 255}}, {{30, 158, 136, 255}},"""				
                f"""{{30, 159, 136, 255}}, {{30, 160, 135, 255}}, {{31, 161, 135, 255}}, {{31, 162, 134, 255}},"""				
                f"""{{31, 163, 134, 255}}, {{32, 164, 133, 255}}, {{32, 165, 133, 255}}, {{33, 166, 133, 255}},"""				
                f"""{{33, 167, 132, 255}}, {{34, 167, 132, 255}}, {{35, 168, 131, 255}}, {{35, 169, 130, 255}},"""				
                f"""{{36, 170, 130, 255}}, {{37, 171, 129, 255}}, {{38, 172, 129, 255}}, {{39, 173, 128, 255}},"""				
                f"""{{40, 174, 127, 255}}, {{41, 175, 127, 255}}, {{42, 176, 126, 255}}, {{43, 177, 125, 255}},"""				
                f"""{{44, 177, 125, 255}}, {{46, 178, 124, 255}}, {{47, 179, 123, 255}}, {{48, 180, 122, 255}},"""			
                f"""{{50, 181, 122, 255}}, {{51, 182, 121, 255}}, {{53, 183, 120, 255}}, {{54, 184, 119, 255}},"""				
                f"""{{56, 185, 118, 255}}, {{57, 185, 118, 255}}, {{59, 186, 117, 255}}, {{61, 187, 116, 255}},"""				
                f"""{{62, 188, 115, 255}}, {{64, 189, 114, 255}}, {{66, 190, 113, 255}}, {{68, 190, 112, 255}},"""				
                f"""{{69, 191, 111, 255}}, {{71, 192, 110, 255}}, {{73, 193, 109, 255}}, {{75, 194, 108, 255}},"""				
                f"""{{77, 194, 107, 255}}, {{79, 195, 105, 255}}, {{81, 196, 104, 255}}, {{83, 197, 103, 255}},"""				
                f"""{{85, 198, 102, 255}}, {{87, 198, 101, 255}}, {{89, 199, 100, 255}}, {{91, 200, 98, 255}},"""				
                f"""{{94, 201, 97, 255}}, {{96, 201, 96, 255}}, {{98, 202, 95, 255}}, {{100, 203, 93, 255}},"""			
                f"""{{103, 204, 92, 255}}, {{105, 204, 91, 255}}, {{107, 205, 89, 255}}, {{109, 206, 88, 255}},"""			
                f"""{{112, 206, 86, 255}}, {{114, 207, 85, 255}}, {{116, 208, 84, 255}}, {{119, 208, 82, 255}},"""				
                f"""{{121, 209, 81, 255}}, {{124, 210, 79, 255}}, {{126, 210, 78, 255}}, {{129, 211, 76, 255}},"""				
                f"""{{131, 211, 75, 255}}, {{134, 212, 73, 255}}, {{136, 213, 71, 255}}, {{139, 213, 70, 255}},"""				
                f"""{{141, 214, 68, 255}}, {{144, 214, 67, 255}}, {{146, 215, 65, 255}}, {{149, 215, 63, 255}},"""				
                f"""{{151, 216, 62, 255}}, {{154, 216, 60, 255}}, {{157, 217, 58, 255}}, {{159, 217, 56, 255}},"""				
                f"""{{162, 218, 55, 255}}, {{165, 218, 53, 255}}, {{167, 219, 51, 255}}, {{170, 219, 50, 255}},"""				
                f"""{{173, 220, 48, 255}}, {{175, 220, 46, 255}}, {{178, 221, 44, 255}}, {{181, 221, 43, 255}},"""				
                f"""{{183, 221, 41, 255}}, {{186, 222, 39, 255}}, {{189, 222, 38, 255}}, {{191, 223, 36, 255}},"""				
                f"""{{194, 223, 34, 255}}, {{197, 223, 33, 255}}, {{199, 224, 31, 255}}, {{202, 224, 30, 255}},"""				
                f"""{{205, 224, 29, 255}}, {{207, 225, 28, 255}}, {{210, 225, 27, 255}}, {{212, 225, 26, 255}},"""				
                f"""{{215, 226, 25, 255}}, {{218, 226, 24, 255}}, {{220, 226, 24, 255}}, {{223, 227, 24, 255}},"""				
                f"""{{225, 227, 24, 255}}, {{228, 227, 24, 255}}, {{231, 228, 25, 255}}, {{233, 228, 25, 255}},"""				
                f"""{{236, 228, 26, 255}}, {{238, 229, 27, 255}}, {{241, 229, 28, 255}}, {{243, 229, 30, 255}},"""
                f"""{{246, 230, 31, 255}}, {{248, 230, 33, 255}}, {{250, 230, 34, 255}}, {{253, 253, 253, 255}}"""    
                f"""}};"""
                f'\n',
            ]


            current_view_lines.extend(new_lines_to_add)

        current_view_lines.append(line)

    # Agregar las líneas restantes para la última vista
    if current_view is not None:
    
        new_lines.extend(current_view_lines)
        existing_lines.update(current_view_lines)

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

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]
            
def sort_lines_alphabetically(opt_file):
    try:
        with open(opt_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {opt_file} was not found.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    lines.sort(key=natural_sort_key)

    try:
        with open(opt_file, 'w') as f:
            f.writelines(lines)
        print(f"Lines sorted alphabetically in {opt_file}.")
        return True
    except Exception as e:
        print(f"Error writing to the file {opt_file}: {e}")
        return False
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_opt_file.py file.opt")
    else:
        opt_file = sys.argv[1]
        success = update_opt_file(opt_file)

        if success:
            # Remove duplicates after modification
            remove_duplicates(opt_file)

            # Sort lines alphabetically
            sort_lines_alphabetically(opt_file)

            print(f"{opt_file} modified successfully.")
            input("Press ENTER to close this window.")