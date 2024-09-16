import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import queue
import sys

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
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)
        update_file_list()

def update_file_list():
    folder_path = folder_entry.get()
    recursive = recursive_var.get()
    python_files = find_python_files(folder_path, recursive)
    for widget in file_frame.winfo_children():
        widget.destroy()
    for file in python_files:
        var = tk.BooleanVar()
        chk = ctk.CTkCheckBox(file_frame, text=file, variable=var)
        chk.var = var
        chk.pack(anchor='w')

def convert_files():
    folder_path = folder_entry.get()
    selected_files = [chk.cget("text") for chk in file_frame.winfo_children() if chk.var.get()]
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
    # Busca el ejecutable en el mismo directorio que main.exe
    executable_path = os.path.join(os.path.dirname(sys.executable), 'Convert_to_csv.exe')
    
    # Verifica si el archivo existe
    if not os.path.isfile(executable_path):
        print(f"Error: No se encontró el archivo ejecutable en {executable_path}")
        return
    
    process = subprocess.Popen([executable_path, folder_path, file] + export_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        print(line, end='')
    for line in process.stderr:
        print(line, end='')

def clear_log():
    log_text.delete(1.0, tk.END)

app = ctk.CTk()
app.title("MSH file converter")

folder_frame = ctk.CTkFrame(app)
folder_frame.pack(pady=10, padx=10, fill='x')

folder_label = ctk.CTkLabel(folder_frame, text="Select Folder:")
folder_label.pack(side='left', padx=5)

folder_entry = ctk.CTkEntry(folder_frame, width=300)
folder_entry.pack(side='left', padx=5)

folder_button = ctk.CTkButton(folder_frame, text="Browse", command=select_folder)
folder_button.pack(side='left', padx=5)

recursive_var = tk.BooleanVar(value=True)
recursive_check = ctk.CTkCheckBox(folder_frame, text="Recursive", variable=recursive_var)
recursive_check.select()
recursive_check.pack(side='left', padx=5)

file_frame = ctk.CTkFrame(app)
file_frame.pack(pady=10, padx=10, fill='both', expand=True)

convert_button = ctk.CTkButton(app, text="Convert", command=convert_files)
convert_button.pack(pady=10)

export_von_misses_var = tk.BooleanVar(value=True)
export_von_misses_check = ctk.CTkCheckBox(app, text="Export Von Misses Stress CSV", variable=export_von_misses_var)
export_von_misses_check.select()
export_von_misses_check.pack(pady=5)

export_smooth_stress_var = tk.BooleanVar(value=True)
export_smooth_stress_check = ctk.CTkCheckBox(app, text="Export Smooth Stress Tensor CSV", variable=export_smooth_stress_var)
export_smooth_stress_check.select()
export_smooth_stress_check.pack(pady=5)

export_vtk_var = tk.BooleanVar(value=True)
export_vtk_check = ctk.CTkCheckBox(app, text="Export VTK", variable=export_vtk_var)
export_vtk_check.select()
export_vtk_check.pack(pady=5)

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