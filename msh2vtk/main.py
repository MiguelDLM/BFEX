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
    
    for file in python_files:
        var = tk.BooleanVar()
        chk = ctk.CTkCheckBox(file_frame_inner, text=file, variable=var, text_color=text_color)
        chk.var = var
        chk.pack(anchor='w', fill='x')

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
    folder_path = folder_entry.get()
    selected_files = [chk.cget("text") for chk in file_frame_inner.winfo_children() if chk.var.get()]
    if not selected_files:
        messagebox.showwarning("No files selected", "Please select at least one file to convert.")
        return

    export_options = []
    if export_von_misses_var.get():
        export_options.append("--export-von-misses")
    if export_smooth_stress_var.get():
        export_options.append("--export-smooth-stress")
    if export_vtk_var.get():
        export_options.append("--export-vtk")

    for file in selected_files:
        threading.Thread(target=run_conversion, args=(folder_path, file, export_options)).start()

def run_conversion(folder_path, file, export_options):
    # Determine the executable name based on the operating system
    if platform.system() == "Windows":
        executable_name = 'Convert_to_csv.exe'
    else:
        executable_name = 'Convert_to_csv'
    
    # Find the executable in the same directory as the main executable
    executable_path = os.path.join(os.path.dirname(sys.executable), executable_name)
    
    # Check if the file exists
    if not os.path.isfile(executable_path):
        print(f"Error: Executable file not found at {executable_path}")
        return
    
    process = subprocess.Popen([executable_path, folder_path, file] + export_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='')

def clear_log():
    log_text.delete(1.0, tk.END)

# Configurar el tema del sistema
ctk.set_appearance_mode("system")  # Usa el tema del sistema (puede ser "dark" o "light")
ctk.set_default_color_theme("blue")  # Puedes cambiar el tema de color si lo deseas

app = ctk.CTk()
app.title("MSH file converter")

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

# Configurar el color de fondo del canvas para que coincida con el fondo del frame interno
appearance_mode = ctk.get_appearance_mode()
background_color = "#000000" if appearance_mode == "dark" else "#FFFFFF"

file_canvas = tk.Canvas(file_frame, bg=background_color, highlightthickness=0)
file_canvas.pack(side='left', fill='both', expand=True)

scrollbar = tk.Scrollbar(file_frame, orient="vertical", command=file_canvas.yview)
scrollbar.pack(side='right', fill='y')

file_frame_inner = ctk.CTkFrame(file_canvas, fg_color=background_color)
file_canvas.create_window((0, 0), window=file_frame_inner, anchor='nw')

file_frame_inner.bind("<Configure>", lambda e: file_canvas.configure(scrollregion=file_canvas.bbox("all")))
file_canvas.configure(yscrollcommand=scrollbar.set)

export_von_misses_var = tk.BooleanVar(value=True)
export_von_misses_check = ctk.CTkCheckBox(convert_section, text="Export Stress Summary (CSV)", variable=export_von_misses_var)
export_von_misses_check.select()
export_von_misses_check.pack(pady=5)

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

app.mainloop()