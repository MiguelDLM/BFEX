import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import queue
import sys
import platform

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass

    def update_text_widget(self):
        while not self.queue.empty():
            string = self.queue.get_nowait()
            self.text_widget.insert(tk.END, string)
            self.text_widget.see(tk.END)
        self.text_widget.after(100, self.update_text_widget)

def find_python_files(directory, recursive):
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
        if not recursive:
            break
    return python_files

def select_folder():
    if platform.system() == "Windows":
        folder_path = filedialog.askdirectory()
    else:
        folder_path = subprocess.run(['zenity', '--file-selection', '--directory'], capture_output=True, text=True).stdout.strip()
    
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)
        update_file_list()

def update_file_list():
    folder_path = folder_entry.get()
    recursive = recursive_var.get()
    python_files = find_python_files(folder_path, recursive)
    for widget in file_frame_inner.winfo_children():
        widget.destroy()
    
    # Configurar el color del texto basado en el modo de apariencia
    appearance_mode = ctk.get_appearance_mode()
    text_color = "#FFFFFF" if appearance_mode == "dark" else "#000000"

    file_checkboxes.clear()
    
    for file in python_files:
        var = tk.BooleanVar()
        chk = ctk.CTkCheckBox(file_frame_inner, text=file, variable=var, text_color=text_color)
        chk.var = var
        chk.pack(anchor='w', fill='x')
        file_checkboxes[file] = chk


def on_conversion_complete(file):
    global progress_count
    progress_count += 1
    progress_bar.set(progress_count / total_files)
    progress_label.configure(text=f"Executing: {progress_count}/{total_files}")
    if file in file_checkboxes:
        file_checkboxes[file].configure(text_color="green")
    # Si se han convertido todos los archivos, mostrar un mensaje
    if progress_count == total_files:
        messagebox.showinfo("Task Complete", "All files have been processed.")
        progress_label.configure(text="Conversion Complete")

def select_fossils_path():
    if platform.system() == "Windows":
        fossils_path = filedialog.askopenfilename(title="Select Fossils Executable", filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")])
    else:
        fossils_path = subprocess.run(['zenity', '--file-selection'], capture_output=True, text=True).stdout.strip()
    
    if fossils_path:
        fossils_entry.delete(0, tk.END)
        fossils_entry.insert(0, fossils_path)

def execute_fossils():
    fossils_path = fossils_entry.get()
    if not fossils_path:
        messagebox.showwarning("No Fossils Path", "Please specify the path to Fossils.")
        return

    selected_files = [chk.cget("text") for chk in file_frame_inner.winfo_children() if chk.var.get()]
    if not selected_files:
        messagebox.showwarning("No files selected", "Please select at least one file to execute with Fossils.")
        return

    for file in selected_files:
        threading.Thread(target=run_fossils, args=(fossils_path, file)).start()

def run_fossils(fossils_path, file):
    if platform.system() == "Windows":
        os.system(f'start cmd /k "{fossils_path} \"{file}\" --nogui"')
    elif platform.system() == "Linux":
        os.system(f'gnome-terminal -- {fossils_path} "{file}" --nogui')

def convert_files():
    global progress_count, total_files
    folder_path = folder_entry.get()
    selected_files = [chk.cget("text") for chk in file_frame_inner.winfo_children() if chk.var.get()]
    if not selected_files:
        messagebox.showwarning("No files selected", "Please select at least one file to convert.")
        return
    
    progress_count = 0
    total_files = len(selected_files)
    progress_bar.set(0)
    progress_label.configure(text=f"Executing: 0/{total_files}")

    export_options = []
    if export_von_mises_var.get():
        export_options.append("--export-von-mises")
    if export_smooth_stress_var.get():
        export_options.append("--export-smooth-stress")
    if export_vtk_var.get():
        export_options.append("--export-vtk")

    for file in selected_files:
        threading.Thread(target=run_conversion, args=(folder_path, file, export_options, on_conversion_complete)).start()

def run_conversion(folder_path, file, export_options, callback):

    # Obtener la ruta del directorio donde se encuentra el archivo main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determinar el nombre del ejecutable o script basado en el sistema operativo
    if platform.system() == "Windows":
        executable_name = 'Convert_to_csv.exe'
    else:
        executable_name = 'Convert_to_csv'
    
    # Construir la ruta completa al ejecutable o script
    executable_path = os.path.join(base_dir, executable_name)
    script_path = os.path.join(base_dir, 'Convert_to_csv.py')
    
    # Verificar si el archivo es un ejecutable o un script Python
    if os.path.isfile(executable_path):
        command = [executable_path, folder_path, file] + export_options
    elif os.path.isfile(script_path):
        command = [sys.executable, script_path, folder_path, file] + export_options
    else:
        print(f"Error: Neither executable nor script file found at {executable_path} or {script_path}")
        return
    
    # Ejecutar el comando
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='')
    callback(file)
def clear_log():
    log_text.delete(1.0, tk.END)


# Configurar el tema del sistema
ctk.set_appearance_mode("system")  # Usa el tema del sistema (puede ser "dark" o "light")
ctk.set_default_color_theme("blue")  # Puedes cambiar el tema de color si lo deseas

app = ctk.CTk()
app.title("MSH file converter")
app.resizable(True, True)

# Sección para ejecutar Fossils
fossils_section = ctk.CTkFrame(app)
fossils_section.pack(pady=10, padx=10, fill='x')

fossils_label = ctk.CTkLabel(fossils_section, text="Fossils Path:")
fossils_label.pack(side='left', padx=5)

fossils_entry = ctk.CTkEntry(fossils_section)
fossils_entry.pack(side='left', padx=5, fill='x', expand=True)

fossils_button = ctk.CTkButton(fossils_section, text="Browse", command=select_fossils_path)
fossils_button.pack(side='right', padx=5)

# Sección para convertir archivos
convert_section = ctk.CTkFrame(app)
convert_section.pack(pady=10, padx=10, fill='x')

folder_frame = ctk.CTkFrame(convert_section)
folder_frame.pack(pady=10, padx=10, fill='x')

folder_label = ctk.CTkLabel(folder_frame, text="Select Folder:")
folder_label.pack(side='left', padx=5)

folder_entry = ctk.CTkEntry(folder_frame)
folder_entry.pack(side='left', padx=5, fill='x', expand=True)

recursive_var = tk.BooleanVar(value=True)
recursive_check = ctk.CTkCheckBox(folder_frame, text="Recursive", variable=recursive_var)
recursive_check.select()
recursive_check.pack(side='right', padx=5)

folder_button = ctk.CTkButton(folder_frame, text="Browse", command=select_folder)
folder_button.pack(side='right', padx=5)

# Marco para la lista de archivos con scrollbar
file_frame = ctk.CTkFrame(convert_section)
file_frame.pack(pady=10, padx=10, fill='both', expand=True)

# Sub-frame para agrupar el Canvas y el scrollbar vertical
canvas_frame = ctk.CTkFrame(file_frame)
canvas_frame.pack(side='top', fill='both', expand=True)

appearance_mode = ctk.get_appearance_mode()
background_color = "#000000" if appearance_mode == "dark" else "#FFFFFF"

file_canvas = tk.Canvas(canvas_frame, bg=background_color, highlightthickness=0, xscrollincrement=20)
file_canvas.pack(side='left', fill='both', expand=True)

scrollbar_y = tk.Scrollbar(canvas_frame, orient="vertical", command=file_canvas.yview)
scrollbar_y.pack(side='right', fill='y')

file_frame_inner = ctk.CTkFrame(file_canvas, fg_color=background_color)
file_canvas.create_window((0, 0), window=file_frame_inner, anchor='nw')

file_frame_inner.bind("<Configure>", lambda e: file_canvas.configure(scrollregion=file_canvas.bbox("all")))
file_canvas.configure(yscrollcommand=scrollbar_y.set)

# Scroll horizontal en la parte inferior, abarcando toda la anchura disponible
scrollbar_x = tk.Scrollbar(file_frame, orient="horizontal", command=file_canvas.xview)
scrollbar_x.pack(side='bottom', fill='x')
file_canvas.configure(xscrollcommand=scrollbar_x.set)

export_von_mises_var = tk.BooleanVar(value=True)
export_von_mises_check = ctk.CTkCheckBox(convert_section, text="Export Stress Summary (CSV)", variable=export_von_mises_var)
export_von_mises_check.select()
export_von_mises_check.pack(pady=5)

export_smooth_stress_var = tk.BooleanVar(value=True)
export_smooth_stress_check = ctk.CTkCheckBox(convert_section, text="Export Stress and Forces (CSV)", variable=export_smooth_stress_var)
export_smooth_stress_check.select()
export_smooth_stress_check.pack(pady=5)

export_vtk_var = tk.BooleanVar(value=True)
export_vtk_check = ctk.CTkCheckBox(convert_section, text="Export VTK", variable=export_vtk_var)
export_vtk_check.select()
export_vtk_check.pack(pady=5)

# Botones de acción
action_buttons_frame = ctk.CTkFrame(app)
action_buttons_frame.pack(pady=10, padx=10, fill='x', expand=True)

# Marco adicional para centrar los botones
buttons_inner_frame = ctk.CTkFrame(action_buttons_frame)
buttons_inner_frame.pack(anchor='center')

execute_fossils_button = ctk.CTkButton(buttons_inner_frame, text="Execute Fossils", command=execute_fossils)
execute_fossils_button.pack(side='left', padx=5)

convert_button = ctk.CTkButton(buttons_inner_frame, text="Convert", command=convert_files)
convert_button.pack(side='left', padx=5)

progress_bar = ctk.CTkProgressBar(app, width=300)
progress_bar.pack(pady=5)
progress_bar.set(0)

progress_label = ctk.CTkLabel(app, text="0/0")
progress_label.pack()

# Sección de log
log_frame = ctk.CTkFrame(app)
log_frame.pack(pady=10, padx=10, fill='both', expand=True)

log_text = tk.Text(log_frame, height=10, wrap='word')
log_text.pack(pady=10, padx=10, fill='both', expand=True)

clear_log_button = ctk.CTkButton(app, text="Clear Log", command=clear_log)
clear_log_button.pack(pady=10)

redirect_text = RedirectText(log_text)
sys.stdout = redirect_text
sys.stderr = redirect_text
redirect_text.update_text_widget()

# checkboxes para marcar finalización de proceso
file_checkboxes = {}
progress_count = 0
total_files = 0

app.mainloop()