import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import queue
import sys
import platform
import json
import requests
import datetime
import time
# Heavy libraries are loaded lazily to reduce startup time
gmsh = None
pv = None
vtk = None
np = None
pd = None

# ``None`` indicates we haven't tried loading yet
MSH_PROCESSING_AVAILABLE = None


def ensure_msh_libraries():
    """Load optional MSH processing libraries on demand."""
    global gmsh, pv, vtk, np, pd, MSH_PROCESSING_AVAILABLE

    if MSH_PROCESSING_AVAILABLE is not None:
        return MSH_PROCESSING_AVAILABLE

    try:
        import numpy as _np
        import pandas as _pd
        import gmsh as _gmsh
        import pyvista as _pv
        from pyvista import _vtk as _vtk

        np = _np
        pd = _pd
        gmsh = _gmsh
        pv = _pv
        vtk = _vtk

        MSH_PROCESSING_AVAILABLE = True
        print("✅ MSH processing libraries available (gmsh, pyvista)")
    except ImportError as e:
        MSH_PROCESSING_AVAILABLE = False
        print(f"⚠️  MSH processing libraries not available: {e}")
        print("   Install with: pip install gmsh pyvista numpy pandas")

    return MSH_PROCESSING_AVAILABLE

# Telegram Configuration
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_ENABLED = False

# Fossils Configuration
FOSSILS_PATH = ""
MAX_PARALLEL_PROCESSES = 1  # Default: run one at a time

# Running processes tracking
running_processes = []
fossils_status_label_main = None
fossils_queue = []  # Queue for pending files

def load_fossils_config():
    """Load Fossils configuration from file"""
    global FOSSILS_PATH, MAX_PARALLEL_PROCESSES
    
    config_file = "fossils_config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                FOSSILS_PATH = config.get('fossils_path', '')
                loaded_parallel = config.get('max_parallel_processes', 1)
                
                # Ensure minimum value is 1
                if loaded_parallel < 1:
                    loaded_parallel = 1
                    print("⚠️  Invalid parallel processes value in config, setting to 1")
                
                MAX_PARALLEL_PROCESSES = loaded_parallel
                
                # Log warning for high values
                if MAX_PARALLEL_PROCESSES > 10:
                    print(f"⚠️  WARNING: Loaded high parallel process count ({MAX_PARALLEL_PROCESSES}) from config. This may cause system resource issues.")
                
                return True
        except Exception as e:
            print(f"⚠️  Error reading Fossils configuration: {e}")
    
    return False

def save_fossils_config(fossils_path, max_parallel=None):
    """Save Fossils configuration to file"""
    global FOSSILS_PATH, MAX_PARALLEL_PROCESSES
    
    # If max_parallel is not provided, keep the current value
    if max_parallel is not None:
        # Ensure minimum value is 1
        if max_parallel < 1:
            max_parallel = 1
        MAX_PARALLEL_PROCESSES = max_parallel
        
        # Log warning for high values
        if max_parallel > 10:
            print(f"⚠️  WARNING: High parallel process count set ({max_parallel}). This may cause system resource issues.")
    
    config = {
        "fossils_path": fossils_path,
        "max_parallel_processes": MAX_PARALLEL_PROCESSES
    }
    
    try:
        with open("fossils_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        FOSSILS_PATH = fossils_path
        return True
    except Exception as e:
        print(f"❌ Error saving Fossils configuration: {e}")
        return False

def start_next_fossils_process():
    """Start the next process from the queue if there's room"""
    global running_processes, fossils_queue, MAX_PARALLEL_PROCESSES
    
    if len(running_processes) < MAX_PARALLEL_PROCESSES and fossils_queue:
        next_file = fossils_queue.pop(0)
        print(f"🔄 Starting next queued process for: {os.path.basename(next_file)}")
        thread = threading.Thread(target=run_fossils, args=(FOSSILS_PATH, next_file))
        thread.daemon = True
        thread.start()

def load_telegram_config():
    """Load Telegram configuration from file"""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
    
    config_file = "telegram_config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                TELEGRAM_BOT_TOKEN = config.get('bot_token', '')
                TELEGRAM_CHAT_ID = config.get('chat_id', '')
                TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
                return True
        except Exception as e:
            print(f"⚠️  Error reading Telegram configuration: {e}")
    
    return False

def save_telegram_config(bot_token, chat_id):
    """Save Telegram configuration to file"""
    config = {
        "bot_token": bot_token,
        "chat_id": chat_id
    }
    
    try:
        with open("telegram_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def test_telegram_connection(bot_token, chat_id):
    """Test Telegram connection"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🧪 Connection test - MSH2VTK configured correctly!',
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error connecting to Telegram: {e}")
        return False

def send_telegram_message(message, silent=False):
    """Send a message to Telegram"""
    if not TELEGRAM_ENABLED:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_notification': silent
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"⚠️  Error sending Telegram message: {e}")
        return False

def open_settings_window():
    """Open settings window for Telegram and Fossils configuration"""
    settings_window = ctk.CTkToplevel(app)
    settings_window.title("Settings")
    settings_window.geometry("600x800")
    settings_window.resizable(False, False)
    
    # Center the window
    settings_window.geometry("+%d+%d" % (app.winfo_rootx()+50, app.winfo_rooty()+50))
    
    # Make it modal after window is created and positioned
    settings_window.transient(app)
    
    # Ensure window is visible before grabbing focus
    settings_window.update_idletasks()
    settings_window.after(10, lambda: settings_window.grab_set())
    
    # Main title
    title_label = ctk.CTkLabel(settings_window, text="⚙️ Application Settings", 
                               font=ctk.CTkFont(size=20, weight="bold"))
    title_label.pack(pady=20)
    
    # Create tabview for different settings sections
    tabview = ctk.CTkTabview(settings_window)
    tabview.pack(pady=10, padx=20, fill='both', expand=True)
    
    # Add tabs (Fossils first, then Telegram)
    fossils_tab = tabview.add("Fossils")
    telegram_tab = tabview.add("Telegram")
    
    # ==================== TELEGRAM TAB ====================
    
    # ==================== TELEGRAM TAB ====================
    
    # Instructions frame for Telegram
    instructions_frame = ctk.CTkFrame(telegram_tab)
    instructions_frame.pack(pady=10, padx=20, fill='x')
    
    instructions_text = """To receive notifications you need:
1. Create a bot in Telegram (@BotFather)
2. Get the bot token
3. Get your Chat ID:
   • Send a message to your bot
   • Visit: https://api.telegram.org/bot<TOKEN>/getUpdates
   • Look for the 'id' value in the 'chat' field"""
    
    instructions_label = ctk.CTkLabel(instructions_frame, text=instructions_text, 
                                      justify="left", wraplength=450)
    instructions_label.pack(pady=10, padx=10)
    
    # Configuration frame for Telegram
    config_frame = ctk.CTkFrame(telegram_tab)
    config_frame.pack(pady=20, padx=20, fill='x')
    
    # Bot Token
    token_label = ctk.CTkLabel(config_frame, text="Bot Token:")
    token_label.pack(pady=(10, 5))
    
    token_entry = ctk.CTkEntry(config_frame, width=400, placeholder_text="Enter your bot token")
    token_entry.pack(pady=(0, 10))
    
    # Chat ID
    chatid_label = ctk.CTkLabel(config_frame, text="Chat ID:")
    chatid_label.pack(pady=(10, 5))
    
    chatid_entry = ctk.CTkEntry(config_frame, width=400, placeholder_text="Enter your Chat ID")
    chatid_entry.pack(pady=(0, 10))
    
    # Load existing configuration or temporary values
    config_file = "telegram_config.json"
    temp_token = ""
    temp_chat_id = ""
    
    # Try to load from config file first
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                temp_token = config.get('bot_token', '')
                temp_chat_id = config.get('chat_id', '')
        except Exception:
            pass
    
    # If no config file, try current global values
    if not temp_token and TELEGRAM_BOT_TOKEN:
        temp_token = TELEGRAM_BOT_TOKEN
    if not temp_chat_id and TELEGRAM_CHAT_ID:
        temp_chat_id = TELEGRAM_CHAT_ID
    
    # Insert values into entries
    if temp_token:
        token_entry.insert(0, temp_token)
    if temp_chat_id:
        chatid_entry.insert(0, temp_chat_id)
    
    # Status label for Telegram
    telegram_status_label = ctk.CTkLabel(config_frame, text="")
    telegram_status_label.pack(pady=10)
    
    def save_telegram_config_only():
        """Save Telegram configuration without testing"""
        bot_token = token_entry.get().strip()
        chat_id = chatid_entry.get().strip()
        
        if not bot_token or not chat_id:
            telegram_status_label.configure(text="❌ Please complete both fields", text_color="red")
            return False
        
        if save_telegram_config(bot_token, chat_id):
            global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
            TELEGRAM_BOT_TOKEN = bot_token
            TELEGRAM_CHAT_ID = chat_id
            TELEGRAM_ENABLED = True
            
            telegram_status_label.configure(text="💾 Configuration saved successfully", text_color="green")
            update_telegram_status_label()
            return True
        else:
            telegram_status_label.configure(text="❌ Error saving configuration", text_color="red")
            return False
    
    def test_telegram_only():
        """Test Telegram connection without saving"""
        bot_token = token_entry.get().strip()
        chat_id = chatid_entry.get().strip()
        
        if not bot_token or not chat_id:
            telegram_status_label.configure(text="❌ Please complete both fields", text_color="red")
            return
        
        telegram_status_label.configure(text="🔄 Testing connection...", text_color="orange")
        settings_window.update()
        
        def test_connection():
            if test_telegram_connection(bot_token, chat_id):
                telegram_status_label.configure(text="✅ Connection test successful!", text_color="green")
            else:
                telegram_status_label.configure(text="❌ Connection test failed. Check your data", text_color="red")
        
        # Run test in thread to avoid blocking UI
        threading.Thread(target=test_connection, daemon=True).start()
    
    def disable_telegram():
        """Disable Telegram notifications"""
        global TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        TELEGRAM_ENABLED = False
        TELEGRAM_BOT_TOKEN = ""
        TELEGRAM_CHAT_ID = ""
        
        try:
            if os.path.exists("telegram_config.json"):
                os.remove("telegram_config.json")
            
            # Clear the input fields
            token_entry.delete(0, tk.END)
            chatid_entry.delete(0, tk.END)
            
            telegram_status_label.configure(text="❌ Telegram disabled and configuration cleared", text_color="orange")
            update_telegram_status_label()
        except Exception as e:
            telegram_status_label.configure(text=f"Error: {e}", text_color="red")
    
    # Telegram buttons frame
    telegram_buttons_frame = ctk.CTkFrame(telegram_tab)
    telegram_buttons_frame.pack(pady=20, padx=20, fill='x')
    
    # Left side buttons for Telegram
    telegram_left_buttons = ctk.CTkFrame(telegram_buttons_frame)
    telegram_left_buttons.pack(side='left', fill='x', expand=True)
    
    save_telegram_button = ctk.CTkButton(telegram_left_buttons, text="💾 Save", command=save_telegram_config_only)
    save_telegram_button.pack(side='left', padx=5)
    
    test_telegram_button = ctk.CTkButton(telegram_left_buttons, text="🧪 Test", command=test_telegram_only)
    test_telegram_button.pack(side='left', padx=5)
    
    disable_telegram_button = ctk.CTkButton(telegram_left_buttons, text="🚫 Disable", command=disable_telegram,
                                   fg_color="red", hover_color="darkred")
    disable_telegram_button.pack(side='left', padx=5)
    
    # ==================== FOSSILS TAB ====================
    
    # Fossils path configuration frame
    fossils_config_frame = ctk.CTkFrame(fossils_tab)
    fossils_config_frame.pack(pady=20, padx=20, fill='x')
    
    fossils_title_label = ctk.CTkLabel(fossils_config_frame, text="Fossils Executable Path", 
                                       font=ctk.CTkFont(size=16, weight="bold"))
    fossils_title_label.pack(pady=(10, 20))
    
    # Path selection row - all in one line
    path_row_frame = ctk.CTkFrame(fossils_config_frame)
    path_row_frame.pack(pady=(0, 15), fill='x', padx=10)
    
    # Current path label
    current_fossils_label = ctk.CTkLabel(path_row_frame, text="Current path:", width=100)
    current_fossils_label.pack(side='left', padx=(10, 10))
    
    # Path input field - expandable
    fossils_path_display = ctk.CTkEntry(path_row_frame, height=32, placeholder_text="No path selected...")
    fossils_path_display.pack(side='left', fill='x', expand=True, padx=(0, 10))
    
    # Load current fossils path
    if FOSSILS_PATH:
        fossils_path_display.insert(0, FOSSILS_PATH)
    
    def select_fossils_path_in_settings():
        """Enhanced file browser for selecting Fossils executable"""
        import os
        from tkinter import filedialog
        
        # Set better initial directory
        initial_dir = "/"
        if FOSSILS_PATH:
            initial_dir = os.path.dirname(FOSSILS_PATH)
        elif os.path.exists("/usr/bin"):
            initial_dir = "/usr/bin"
        
        # More comprehensive file dialog
        fossils_path = filedialog.askopenfilename(
            title="Select Fossils Executable - Navigate to your Fossils installation",
            initialdir=initial_dir,
            filetypes=[
                ("Executable Files", "*"),
                ("All Files", "*.*"),
                ("Binary Files", "*.bin"),
                ("Application Files", "*.app"),
                ("Script Files", "*.sh"),
                ("Python Files", "*.py")
            ],
            multiple=False
        )
        
        if fossils_path:
            fossils_path_display.delete(0, tk.END)
            fossils_path_display.insert(0, fossils_path)
            fossils_status_label.configure(text="✅ Path selected successfully", text_color="green")
            
            # Validate if file is executable
            if os.path.isfile(fossils_path):
                if os.access(fossils_path, os.X_OK):
                    fossils_status_label.configure(text="✅ Valid executable selected", text_color="green")
                else:
                    fossils_status_label.configure(text="⚠️ File selected but may not be executable", text_color="orange")
            else:
                fossils_status_label.configure(text="❌ Selected path is not a valid file", text_color="red")
    
    # Browse button
    browse_fossils_button = ctk.CTkButton(
        path_row_frame, 
        text="📁 Browse", 
        command=select_fossils_path_in_settings, 
        width=100,
        height=32
    )
    browse_fossils_button.pack(side='right', padx=(0, 10))
    
    # ==================== PARALLEL PROCESSES CONFIGURATION ====================
    
    # Parallel processes configuration frame
    parallel_config_frame = ctk.CTkFrame(fossils_tab)
    parallel_config_frame.pack(pady=20, padx=20, fill='x')
    
    parallel_title_label = ctk.CTkLabel(parallel_config_frame, text="Parallel Processes Configuration", 
                                       font=ctk.CTkFont(size=16, weight="bold"))
    parallel_title_label.pack(pady=(10, 20))
    
    # Current setting display
    current_parallel_label = ctk.CTkLabel(parallel_config_frame, text="Maximum parallel processes:")
    current_parallel_label.pack(pady=(0, 5))
    
    # Number input for selecting max parallel processes
    parallel_entry = ctk.CTkEntry(parallel_config_frame, width=100, height=30, justify="center")
    parallel_entry.pack(pady=(0, 10))
    parallel_entry.insert(0, str(MAX_PARALLEL_PROCESSES))
    
    # Warning label for high values (initially hidden)
    warning_label = ctk.CTkLabel(parallel_config_frame, 
                                text="⚠️ WARNING: This number is very high and may exhaust your computer's RAM,\ncausing analyses to stop. Values between 1-10 are recommended.",
                                font=ctk.CTkFont(size=12),
                                text_color="orange",
                                wraplength=450)
    
    # Helper text
    helper_text = ctk.CTkLabel(parallel_config_frame, 
                              text="💡 Recommended: 1-4 for most systems\n📊 Powerful systems: 5-10",
                              font=ctk.CTkFont(size=12),
                              text_color="gray")
    helper_text.pack(pady=(5, 10))
    
    # Function to validate and show warnings for parallel processes input
    def validate_parallel_input():
        try:
            value = int(parallel_entry.get())
            if value > 10:
                warning_label.pack(pady=(5, 10))
            else:
                warning_label.pack_forget()
            return True
        except ValueError:
            # If invalid number, show nothing but don't prevent saving
            warning_label.pack_forget()
            return True
    
    # Bind validation to entry changes
    parallel_entry.bind('<KeyRelease>', lambda event: validate_parallel_input())
    
    # ==================== CENTERED SAVE BUTTON WITH STATUS ====================
    
    # Centered save button frame
    save_button_frame = ctk.CTkFrame(fossils_tab)
    save_button_frame.pack(pady=30, padx=20, fill='x')
    
    # Status label for Fossils - positioned right above save button
    fossils_status_label = ctk.CTkLabel(save_button_frame, text="")
    fossils_status_label.pack(pady=(10, 15))
    
    # Update save_fossils_path function to also save parallel setting
    def save_fossils_path_with_parallel():
        """Save Fossils path and parallel processes setting"""
        path = fossils_path_display.get().strip()
        
        try:
            max_parallel = int(parallel_entry.get())
            if max_parallel < 1:
                fossils_status_label.configure(text="❌ Number of processes must be greater than 0", text_color="red")
                return
        except ValueError:
            fossils_status_label.configure(text="❌ Please enter a valid number for parallel processes", text_color="red")
            return
        
        if path:
            if save_fossils_config(path, max_parallel):
                if max_parallel > 10:
                    fossils_status_label.configure(text=f"💾 Configuration saved (Max parallel: {max_parallel}) ⚠️ High value detected", text_color="orange")
                else:
                    fossils_status_label.configure(text=f"💾 Configuration saved successfully (Max parallel: {max_parallel})", text_color="green")
            else:
                fossils_status_label.configure(text="❌ Error saving configuration", text_color="red")
        else:
            fossils_status_label.configure(text="❌ Please select a path first", text_color="red")
    
    save_fossils_button = ctk.CTkButton(save_button_frame, text="💾 Save Configuration", 
                                       command=save_fossils_path_with_parallel, 
                                       width=200, height=40,
                                       font=ctk.CTkFont(size=14, weight="bold"))
    save_fossils_button.pack(pady=(0, 10))
    
    # ==================== CLOSE BUTTON ====================
    
    # Close button at the bottom
    close_button = ctk.CTkButton(settings_window, text="Close", command=settings_window.destroy)
    close_button.pack(pady=20)

def update_telegram_status_label():
    """Update the Telegram status label in main window"""
    if TELEGRAM_ENABLED:
        telegram_status_label.configure(text="📱 Telegram: ENABLED", text_color="green")
    else:
        telegram_status_label.configure(text="📱 Telegram: DISABLED", text_color="red")

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
    
    # Send individual file completion notification
    if TELEGRAM_ENABLED:
        message = f"✅ <b>File Completed</b>\n📁 {os.path.basename(file)}\n📊 {progress_count}/{total_files}"
        send_telegram_message(message, silent=True)
    
    # If all files have been converted, show a message
    if progress_count == total_files:
        messagebox.showinfo("Task Complete", "All files have been processed.")
        progress_label.configure(text="Conversion Complete")
        
        # Send completion summary to Telegram
        if TELEGRAM_ENABLED:
            summary_message = f"🎉 <b>MSH2VTK - Conversion Completed</b>\n📁 Total: {total_files} files\n🕐 Finished: {datetime.datetime.now().strftime('%H:%M:%S')}"
            send_telegram_message(summary_message)

def select_fossils_path():
    fossils_path = filedialog.askopenfilename(
        title="Select Fossils Executable", 
        filetypes=[("Executable Files", "*"), ("All Files", "*.*")]
    )
    
    if fossils_path:
        save_fossils_config(fossils_path)

def cancel_fossils_execution():
    """Cancel all running Fossils processes and clear the queue"""
    global running_processes, fossils_queue
    
    # Cancel running processes
    if running_processes:
        for process in running_processes:
            try:
                process.terminate()
                print(f"🛑 Terminated process: {process.pid}")
            except Exception as e:
                print(f"⚠️  Error terminating process: {e}")
        
        running_processes.clear()
        print("🛑 All Fossils processes cancelled")
    
    # Clear the queue
    if fossils_queue:
        print(f"🛑 Cleared {len(fossils_queue)} queued files")
        fossils_queue.clear()
        
        # Send cancellation notification to Telegram
        if TELEGRAM_ENABLED:
            message = f"🛑 <b>Fossils Execution Cancelled</b>\n🕐 {datetime.datetime.now().strftime('%H:%M:%S')}"
            send_telegram_message(message)
    
    # Reset UI
    execute_fossils_button.configure(state="normal", text="Execute Fossils")
    cancel_fossils_button.configure(state="disabled")
    fossils_status_label_main.configure(text="🛑 Fossils execution cancelled", text_color="red")

def on_fossils_complete():
    """Called when all Fossils processes are complete"""
    global running_processes, fossils_queue
    if not running_processes and not fossils_queue:  # All processes finished and queue is empty
        execute_fossils_button.configure(state="normal", text="Execute Fossils")
        cancel_fossils_button.configure(state="disabled")
        
        # Update status message based on MSH processing availability
        if ensure_msh_libraries():
            fossils_status_label_main.configure(text="✅ All Fossils processes and MSH processing completed", text_color="green")
            completion_message_text = "🎉 <b>MSH2VTK - All Fossils Processes and MSH Processing Completed</b>"
        else:
            fossils_status_label_main.configure(text="✅ All Fossils processes completed (MSH processing unavailable)", text_color="green")
            completion_message_text = "🎉 <b>MSH2VTK - All Fossils Processes Completed</b>\n⚠️ MSH processing was unavailable"
        
        # Send completion notification to Telegram
        if TELEGRAM_ENABLED:
            completion_message = f"{completion_message_text}\n🕐 {datetime.datetime.now().strftime('%H:%M:%S')}"
            send_telegram_message(completion_message)

def execute_fossils():
    print("🔍 DEBUG: execute_fossils() called")
    global FOSSILS_PATH, running_processes, fossils_queue, MAX_PARALLEL_PROCESSES
    print(f"🔍 DEBUG: FOSSILS_PATH = '{FOSSILS_PATH}'")
    print(f"🔍 DEBUG: MAX_PARALLEL_PROCESSES = {MAX_PARALLEL_PROCESSES}")
    
    if not FOSSILS_PATH:
        print("❌ DEBUG: No Fossils path configured")
        messagebox.showwarning("No Fossils Path", "Please configure the Fossils path in Settings.")
        return

    selected_files = [chk.cget("text") for chk in file_frame_inner.winfo_children() if chk.var.get()]
    print(f"🔍 DEBUG: Selected files: {selected_files}")
    
    if not selected_files:
        print("❌ DEBUG: No files selected")
        messagebox.showwarning("No files selected", "Please select at least one file to execute with Fossils.")
        return

    print(f"🚀 DEBUG: Starting Fossils execution for {len(selected_files)} files with max {MAX_PARALLEL_PROCESSES} parallel processes")
    
    # Show warning for high parallel process counts
    if MAX_PARALLEL_PROCESSES > 10:
        print(f"⚠️  WARNING: Using {MAX_PARALLEL_PROCESSES} parallel processes may cause system resource issues!")
    
    # Clear any existing queue and add all selected files
    fossils_queue.clear()
    fossils_queue.extend(selected_files)
    
    # Update UI for execution start
    execute_fossils_button.configure(state="disabled", text="🔄 Running...")
    cancel_fossils_button.configure(state="normal")
    fossils_status_label_main.configure(text=f"🔄 Starting Fossils ({len(selected_files)} files, max {MAX_PARALLEL_PROCESSES} parallel)...", text_color="orange")
    
    # Send start notification to Telegram
    if TELEGRAM_ENABLED:
        start_message = f"🚀 <b>MSH2VTK - Starting Fossils Execution</b>\n📁 {len(selected_files)} files\n⚙️ Max parallel: {MAX_PARALLEL_PROCESSES}\n🕐 {datetime.datetime.now().strftime('%H:%M:%S')}"
        send_telegram_message(start_message)

    # Start initial processes up to the maximum limit
    for _ in range(min(MAX_PARALLEL_PROCESSES, len(fossils_queue))):
        start_next_fossils_process()

def run_fossils(fossils_path, file):
    print(f"🔍 DEBUG: run_fossils() called with fossils_path='{fossils_path}', file='{file}'")
    global running_processes
    process = None
    
    try:
        start_time = time.time()
        command = [fossils_path, file, "--nogui"]
        print(f"🔍 DEBUG: Command to execute: {command}")
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        running_processes.append(process)
        
        print(f"🔄 Started Fossils process PID: {process.pid} for file: {os.path.basename(file)}")
        
        # Update status label to show current file being processed
        queued_count = len(fossils_queue)
        running_count = len(running_processes)
        app.after_idle(lambda: fossils_status_label_main.configure(
            text=f"🔄 Processing: {os.path.basename(file)} ({running_count} running, {queued_count} queued)", 
            text_color="orange"
        ))
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        # Remove process from running list
        if process in running_processes:
            running_processes.remove(process)
        
        print(f"🔍 DEBUG: Command finished with return code: {process.returncode}")
        if stdout:
            print(f"🔍 DEBUG: stdout: {stdout}")
        if stderr:
            print(f"🔍 DEBUG: stderr: {stderr}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if process.returncode == 0:
            print(f"✓ Completed: {os.path.basename(file)} ({execution_time:.2f}s)")
            
            # Rename workspace folder to match the Python file name
            print(f"🔄 Renaming workspace folder for: {os.path.basename(file)}")
            rename_success = rename_workspace_folder(file)
            if rename_success:
                print(f"✅ Workspace folder rename completed for: {os.path.basename(file)}")
            else:
                print(f"⚠️  Workspace folder rename failed for: {os.path.basename(file)}")
            
            # Process MSH files automatically if libraries are available
            if ensure_msh_libraries():
                print(f"🔄 Starting MSH processing for: {os.path.basename(file)}")
                
                # Update status to show MSH processing
                remaining_count = len(running_processes)
                queued_count = len(fossils_queue)
                app.after_idle(lambda: fossils_status_label_main.configure(
                    text=f"🔄 MSH processing: {os.path.basename(file)} ({remaining_count} running, {queued_count} queued)", 
                    text_color="orange"
                ))
                
                try:
                    # Get export settings from UI checkboxes
                    export_vtk = export_vtk_var.get()
                    export_smooth_stress = export_smooth_stress_var.get()
                    export_von_mises = export_von_mises_var.get()
                    
                    # Process the Fossils output using integrated function
                    msh_success = process_fossils_output(
                        file, 
                        export_von_mises=export_von_mises,
                        export_smooth_stress=export_smooth_stress,
                        export_vtk=export_vtk
                    )
                    
                    if msh_success:
                        print(f"✅ MSH processing completed for: {os.path.basename(file)}")
                    else:
                        print(f"⚠️ MSH processing failed for: {os.path.basename(file)}")
                        
                except Exception as e:
                    print(f"❌ Error during MSH processing for {os.path.basename(file)}: {e}")
            else:
                print(f"⚠️ MSH processing skipped (libraries not available) for: {os.path.basename(file)}")
            
            # Update status label with completion info
            remaining_count = len(running_processes)
            queued_count = len(fossils_queue)
            app.after_idle(lambda: fossils_status_label_main.configure(
                text=f"✅ Completed: {os.path.basename(file)} ({remaining_count} running, {queued_count} queued)", 
                text_color="green" if remaining_count == 0 and queued_count == 0 else "orange"
            ))
            
            # Send success notification to Telegram
            if TELEGRAM_ENABLED:
                if ensure_msh_libraries():
                    message = f"✅ <b>Fossils Analysis & MSH Processing Completed</b>\n📁 {os.path.basename(file)}\n⏱️ {execution_time:.2f}s"
                else:
                    message = f"✅ <b>Fossils Analysis Completed</b>\n📁 {os.path.basename(file)}\n⏱️ {execution_time:.2f}s\n⚠️ MSH processing unavailable"
                send_telegram_message(message, silent=True)
        else:
            print(f"✗ Error in: {os.path.basename(file)} (code: {process.returncode})")
            if stderr:
                print(f"  Error: {stderr.strip()}")
            
            # Update status label with error info
            remaining_count = len(running_processes)
            queued_count = len(fossils_queue)
            app.after_idle(lambda: fossils_status_label_main.configure(
                text=f"❌ Error in: {os.path.basename(file)} ({remaining_count} running, {queued_count} queued)", 
                text_color="red"
            ))
            
            # Send error notification to Telegram
            if TELEGRAM_ENABLED:
                message = f"❌ <b>Error in Fossils Analysis</b>\n📁 {os.path.basename(file)}\n🔢 Code: {process.returncode}"
                send_telegram_message(message)
                
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout in: {os.path.basename(file)} (more than 1 hour)")
        
        if process and process in running_processes:
            running_processes.remove(process)
        
        # Update status label with timeout info
        remaining_count = len(running_processes)
        queued_count = len(fossils_queue)
        app.after_idle(lambda: fossils_status_label_main.configure(
            text=f"⏰ Timeout: {os.path.basename(file)} ({remaining_count} running, {queued_count} queued)", 
            text_color="red"
        ))
        
        # Send timeout notification to Telegram
        if TELEGRAM_ENABLED:
            message = f"⏰ <b>Timeout</b>\n📁 {os.path.basename(file)}\n🕐 More than 1 hour"
            send_telegram_message(message)
            
    except Exception as e:
        print(f"✗ Exception in: {os.path.basename(file)} - {str(e)}")
        
        if process and process in running_processes:
            running_processes.remove(process)
        
        # Update status label with exception info
        remaining_count = len(running_processes)
        queued_count = len(fossils_queue)
        app.after_idle(lambda: fossils_status_label_main.configure(
            text=f"💥 Exception: {os.path.basename(file)} ({remaining_count} running, {queued_count} queued)", 
            text_color="red"
        ))
        
        # Send exception notification to Telegram
        if TELEGRAM_ENABLED:
            message = f"💥 <b>Exception</b>\n📁 {os.path.basename(file)}\n⚠️ {str(e)}"
            send_telegram_message(message)
    
    # Start next process from queue if available
    app.after_idle(start_next_fossils_process)
    
    # Check if all processes are complete
    app.after_idle(on_fossils_complete)

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

    # Send start notification to Telegram
    if TELEGRAM_ENABLED:
        start_message = f"🚀 <b>MSH2VTK - Starting Conversion</b>\n📁 {total_files} files\n🕐 {datetime.datetime.now().strftime('%H:%M:%S')}"
        send_telegram_message(start_message)

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

    # Determinar la ubicación base según si estamos ejecutando desde un ejecutable o un script
    if getattr(sys, 'frozen', False):
        # Estamos ejecutando desde un ejecutable de PyInstaller
        # Usar el directorio donde está el ejecutable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Estamos ejecutando desde el script Python normal
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
        print(f"Using executable: {executable_path}")
    elif os.path.isfile(script_path):
        command = [sys.executable, script_path, folder_path, file] + export_options
        print(f"Using script: {script_path}")
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


# Configure system theme
ctk.set_appearance_mode("system")  # Use system theme (can be "dark" or "light")
ctk.set_default_color_theme("blue")  # You can change the color theme if desired

app = ctk.CTk()
app.title("MSH file converter")
app.resizable(True, True)

# Load Telegram configuration at startup
load_telegram_config()

# Load Fossils configuration at startup
load_fossils_config()

# Top frame for settings and status
top_frame = ctk.CTkFrame(app)
top_frame.pack(pady=5, padx=10, fill='x')

# Settings button
settings_button = ctk.CTkButton(top_frame, text="⚙️ Settings", command=open_settings_window, width=100)
settings_button.pack(side='left', padx=5)

# Telegram status label - declare globally
telegram_status_label = ctk.CTkLabel(top_frame, text="📱 Telegram: DISABLED", text_color="red")
telegram_status_label.pack(side='right', padx=5)

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

cancel_fossils_button = ctk.CTkButton(buttons_inner_frame, text="🛑 Cancel Fossils", command=cancel_fossils_execution,
                                     fg_color="red", hover_color="darkred", state="disabled")
cancel_fossils_button.pack(side='left', padx=5)

convert_button = ctk.CTkButton(buttons_inner_frame, text="Convert", command=convert_files)
convert_button.pack(side='left', padx=5)

# Fossils status indicator
fossils_status_label_main = ctk.CTkLabel(app, text="⚪ Fossils: Ready", text_color="gray")
fossils_status_label_main.pack(pady=5)

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

# checkboxes to mark process completion
file_checkboxes = {}
progress_count = 0
total_files = 0

# Update telegram status at startup
update_telegram_status_label()

# ==================== MSH PROCESSING FUNCTIONS ====================

def find_msh_files(python_file):
    """Find MSH files generated by Fossils with enhanced search pattern"""
    base_name = os.path.splitext(os.path.basename(python_file))[0]
    parent_dir = os.path.dirname(python_file)
    
    # Get the directory where the executable is running from
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        script_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of possible locations to search for MSH files
    possible_locations = []
    
    # 1. Same folder as python file (original expected location)
    possible_locations.append(os.path.splitext(python_file)[0])
    
    # 2. Workspace folder in the same directory as python file
    possible_locations.append(os.path.join(parent_dir, "workspace", base_name))
    
    # 3. Workspace folder in the script directory (where main.py is)
    possible_locations.append(os.path.join(script_dir, "workspace", base_name))
    
    # 4. Search for folders that contain part of the python file name in workspace directories
    workspace_dirs = [
        os.path.join(parent_dir, "workspace"),
        os.path.join(script_dir, "workspace")
    ]
    
    for workspace_dir in workspace_dirs:
        if os.path.exists(workspace_dir):
            try:
                for folder_name in os.listdir(workspace_dir):
                    folder_path = os.path.join(workspace_dir, folder_name)
                    if os.path.isdir(folder_path):
                        # Check if the folder name contains the base name of our python file
                        # or if our base name contains part of the folder name
                        if (base_name.lower() in folder_name.lower() or 
                            folder_name.lower() in base_name.lower() or
                            any(word in folder_name.lower() for word in base_name.lower().split('_') if len(word) > 3)):
                            possible_locations.append(folder_path)
            except Exception as e:
                print(f"   ⚠️  Error scanning workspace directory {workspace_dir}: {e}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for location in possible_locations:
        if location not in seen:
            seen.add(location)
            unique_locations.append(location)
    
    print(f"🔍 Searching for MSH files for: {base_name}")
    print(f"   Checking {len(unique_locations)} possible locations...")
    
    # Check each possible location
    for i, folder_path in enumerate(unique_locations, 1):
        print(f"   {i}. Checking: {folder_path}")
        
        if not os.path.exists(folder_path):
            print(f"      ❌ Directory does not exist")
            continue
            
        mesh_file = os.path.join(folder_path, 'mesh.msh')
        stress_tensor_file = os.path.join(folder_path, 'smooth_stress_tensor.msh')
        force_vector_file = os.path.join(folder_path, 'force_vector.msh')

        # Check if all required files exist
        files_exist = [
            os.path.exists(mesh_file),
            os.path.exists(stress_tensor_file),
            os.path.exists(force_vector_file)
        ]
        
        print(f"      📄 mesh.msh: {'✅' if files_exist[0] else '❌'}")
        print(f"      📄 smooth_stress_tensor.msh: {'✅' if files_exist[1] else '❌'}")
        print(f"      📄 force_vector.msh: {'✅' if files_exist[2] else '❌'}")

        if all(files_exist):
            print(f"   ✅ Found all MSH files in: {folder_path}")
            return mesh_file, stress_tensor_file, force_vector_file
    
    # If no files found, show what's in the workspace for debugging
    print(f"❌ MSH files not found in any of the {len(unique_locations)} locations checked")
    
    # Show workspace contents for debugging
    for workspace_dir in workspace_dirs:
        if os.path.exists(workspace_dir):
            print(f"📁 Contents of workspace folder ({workspace_dir}):")
            try:
                for item in os.listdir(workspace_dir):
                    item_path = os.path.join(workspace_dir, item)
                    if os.path.isdir(item_path):
                        print(f"   📂 {item}")
                        # Show MSH files in this folder
                        try:
                            msh_files = [f for f in os.listdir(item_path) if f.endswith('.msh')]
                            if msh_files:
                                print(f"      MSH files: {', '.join(msh_files)}")
                            else:
                                print(f"      No MSH files found")
                        except Exception as e:
                            print(f"      Error listing folder contents: {e}")
            except Exception as e:
                print(f"   Error listing workspace contents: {e}")
    
    return None, None, None

def process_fossils_output(selected_file, export_von_mises=True, export_smooth_stress=True, export_vtk=True):
    """Process Fossils output MSH files and convert them to CSV/VTK"""
    if not ensure_msh_libraries():
        print("❌ MSH processing libraries not available. Skipping conversion.")
        return False
    
    # Import required modules at the beginning to avoid scope issues
    import os
    import signal
    import subprocess
    import tempfile
    import sys
    from contextlib import redirect_stderr
    from io import StringIO
    
    def initialize_gmsh_safely():
        """Initialize gmsh with complete cleanup and multiple fallback strategies"""
        print("🔍 DEBUG: Starting safe gmsh initialization...")
        
        # First, try to completely cleanup any existing gmsh instance
        try:
            print("🔍 DEBUG: Attempting to cleanup any existing gmsh state...")
            
            # Try to access gmsh functions to see if it's initialized
            try:
                # Clear all models first
                model_list = gmsh.model.list()
                for model_name in model_list:
                    gmsh.model.setCurrent(model_name)
                    gmsh.model.remove()
                print(f"🔍 DEBUG: Removed {len(model_list)} existing models")
            except:
                print("🔍 DEBUG: No models to clean")
            
            try:
                # Clear all views
                view_list = gmsh.view.getTags()
                for view_tag in view_list:
                    gmsh.view.remove(view_tag)
                print(f"🔍 DEBUG: Removed {len(view_list)} existing views")
                
                # Additional cleanup for post-processing data
                gmsh.view.removeAllModels()
                print("🔍 DEBUG: Cleared all view models")
            except:
                print("🔍 DEBUG: No views to clear")
            
            try:
                # Force finalize to completely reset gmsh
                gmsh.finalize()
                print("🔍 DEBUG: Existing gmsh instance finalized")
            except:
                print("🔍 DEBUG: No existing gmsh instance to finalize")
                
        except Exception as e:
            print(f"🔍 DEBUG: No existing gmsh state to clean: {e}")
        
        initialization_successful = False
        
        # Strategy 1: Complete signal disabling for PyInstaller
        try:
            print("🔍 DEBUG: Trying PyInstaller-compatible initialization...")
            
            # Store original signal handlers
            original_handlers = {}
            
            # Completely disable all signal handlers that could conflict
            for sig in [signal.SIGINT, signal.SIGTERM]:
                try:
                    original_handlers[sig] = signal.signal(sig, signal.SIG_IGN)
                except (ValueError, OSError):
                    pass  # Signal not available on this platform
            
            # Set environment variables to disable gmsh signal handling
            os.environ['GMSH_NO_SIGNAL'] = '1'
            os.environ['GMSH_NO_INTERRUPT'] = '1'
            
            try:
                # Initialize with comprehensive signal-free arguments
                gmsh.initialize([
                    '-noenv',          # Don't read environment files
                    '-nopopup',        # No popup windows
                    '-notty',          # No TTY interaction
                    '-nosigint',       # No SIGINT handling
                    '-batch',          # Batch mode
                    '-nt',             # Non-interactive
                    '-v', '0'          # Minimal verbosity
                ])
                initialization_successful = True
                print("🔍 DEBUG: PyInstaller-compatible initialization successful")
            finally:
                # Restore original signal handlers
                for sig, handler in original_handlers.items():
                    try:
                        signal.signal(sig, handler)
                    except (ValueError, OSError):
                        pass
                
        except Exception as e:
            print(f"🔍 DEBUG: PyInstaller-compatible initialization failed: {e}")
            
        # Strategy 2: Force-ignore all signal operations  
        if not initialization_successful:
            try:
                print("🔍 DEBUG: Trying force-ignore signal strategy...")
                
                # Create a custom signal handler that does nothing
                def null_handler(signum, frame):
                    pass
                
                # Override signal function temporarily
                original_signal = signal.signal
                def disabled_signal(sig, handler):
                    try:
                        return original_signal(sig, null_handler)
                    except:
                        return signal.SIG_DFL
                
                # Temporarily replace signal.signal
                signal.signal = disabled_signal
                
                try:
                    gmsh.initialize(['-batch', '-nt', '-v', '0'])
                    initialization_successful = True
                    print("🔍 DEBUG: Force-ignore signal strategy successful")
                finally:
                    # Restore original signal function
                    signal.signal = original_signal
                    
            except Exception as e:
                print(f"🔍 DEBUG: Force-ignore signal strategy failed: {e}")
        
        # Strategy 3: Minimal initialization
        if not initialization_successful:
            try:
                print("🔍 DEBUG: Trying minimal initialization...")
                gmsh.initialize()
                initialization_successful = True
                print("🔍 DEBUG: Minimal initialization successful")
            except Exception as e:
                print(f"🔍 DEBUG: Minimal initialization failed: {e}")
        
        return initialization_successful
    
    try:
        mesh_file, stress_tensor_file, force_vector_file = find_msh_files(selected_file)
        
        if not all([mesh_file, stress_tensor_file, force_vector_file]):
            print(f"❌ Cannot find required MSH files for {os.path.basename(selected_file)}")
            return False
        
        folder_path = os.path.dirname(mesh_file)
        print(f"\n🔄 Processing MSH files in {os.path.basename(folder_path)}:")
        print(f"   📄 mesh.msh: {os.path.exists(mesh_file)}")
        print(f"   📄 smooth_stress_tensor.msh: {os.path.exists(stress_tensor_file)}")
        print(f"   📄 force_vector.msh: {os.path.exists(force_vector_file)}")

        print("🔍 DEBUG: Starting gmsh initialization...")
        
        # Use safe initialization function
        if not initialize_gmsh_safely():
            print("❌ All gmsh initialization strategies failed")
            print("   This is a known limitation with PyInstaller and gmsh signal handling")
            return False
        
        # If we got here, gmsh was successfully initialized
        try:
            # Set options to disable interactive features
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("General.Verbosity", 1) 
            gmsh.option.setNumber("General.AbortOnError", 0)
            # Additional options to prevent signal conflicts
            gmsh.option.setNumber("General.NoPopup", 1)
            gmsh.option.setNumber("General.Abort", 0)
            
        except Exception as e:
            print(f"🔍 DEBUG: Warning - failed to set gmsh options: {e}")
            # Continue anyway, as the main initialization worked
        
        print("🔍 DEBUG: gmsh initialized successfully")
        
        # Complete cleanup of any existing gmsh state
        try:
            print("🔍 DEBUG: Cleaning up existing gmsh state...")
            # Clear all existing models
            for model_name in gmsh.model.list():
                gmsh.model.setCurrent(model_name)
                gmsh.model.remove()
            
            # Clear all existing views
            for view_tag in gmsh.view.getTags():
                gmsh.view.remove(view_tag)
            
            # Clear any existing post-processing data
            gmsh.view.removeAllModels()
            
            print("🔍 DEBUG: gmsh state cleaned successfully")
        except Exception as e:
            print(f"🔍 DEBUG: Warning during gmsh cleanup: {e}")
        
        gmsh.model.add("FossilsOutput")
        print("🔍 DEBUG: gmsh model added successfully")
        
        # Load MSH files
        print("🔍 DEBUG: Loading mesh files...")
        gmsh.merge(mesh_file)
        print("🔍 DEBUG: mesh.msh loaded")
        gmsh.merge(stress_tensor_file)
        print("🔍 DEBUG: stress_tensor.msh loaded")
        gmsh.merge(force_vector_file)
        print("🔍 DEBUG: force_vector.msh loaded")
        
        # Debug: Check available views and their data
        view_tags = gmsh.view.getTags()
        print(f"🔍 DEBUG: Available views: {view_tags}")
        
        for view_tag in view_tags:
            try:
                view_name = gmsh.view.getOption(view_tag, "Name")
                print(f"🔍 DEBUG: View {view_tag}: {view_name}")
            except:
                print(f"🔍 DEBUG: View {view_tag}: (name not available)")

        # Get node data
        nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
        nodeCoords = np.array(nodeCoords).reshape((-1, 3))
        nodeData = pd.DataFrame({
            'NodeTag': nodeTags, 
            'X': nodeCoords[:, 0], 
            'Y': nodeCoords[:, 1], 
            'Z': nodeCoords[:, 2]
        })

        # Process stress tensor data with robust error handling
        print("🔍 DEBUG: Processing stress tensor data...")
        view_tags = gmsh.view.getTags()
        
        # Find the stress tensor and force vector views by analyzing data types
        stress_view_tag = None
        force_view_tag = None
        
        # Analyze each view to determine its data type
        for view_tag in view_tags:
            try:
                dataType, tags, data, time, numComp = gmsh.view.getModelData(view_tag, 0)
                print(f"🔍 DEBUG: View {view_tag}: dataType={dataType}, numComp={numComp}, data_len={len(data)}")
                
                # Heuristic to identify stress vs force data
                if len(data) > 0 and len(data[0]) >= 6:
                    # Likely stress tensor data (6 or 9 components)
                    if stress_view_tag is None:
                        stress_view_tag = view_tag
                        print(f"🔍 DEBUG: Identified stress view: {view_tag} (components: {len(data[0])})")
                elif len(data) > 0 and len(data[0]) <= 3:
                    # Likely force vector data (1-3 components)
                    if force_view_tag is None:
                        force_view_tag = view_tag
                        print(f"🔍 DEBUG: Identified force view: {view_tag} (components: {len(data[0])})")
                        
            except Exception as e:
                print(f"🔍 DEBUG: Error analyzing view {view_tag}: {e}")
        
        # Fallback to simple ordering if heuristics fail
        if stress_view_tag is None and len(view_tags) >= 1:
            stress_view_tag = view_tags[0]
            print("🔍 DEBUG: Using fallback stress view (first available)")
        
        if force_view_tag is None and len(view_tags) >= 2:
            force_view_tag = view_tags[1]
            print("🔍 DEBUG: Using fallback force view (second available)")
        
        if stress_view_tag is None:
            raise Exception("No stress tensor view found after loading MSH files")
        
        print(f"🔍 DEBUG: Final stress view tag: {stress_view_tag}")
        print(f"🔍 DEBUG: Final force view tag: {force_view_tag}")
        
        # Process stress tensor data
        try:
            print(f"🔍 DEBUG: Processing stress data from view {stress_view_tag}")
            dataType, tags, data, time, numComp = gmsh.view.getModelData(stress_view_tag, 0)
            print(f"🔍 DEBUG: Stress data - dataType: {dataType}, numComp: {numComp}, data length: {len(data)}")
            
            # Validate data consistency
            if len(data) != len(nodeTags):
                print(f"⚠️ WARNING: Data length mismatch - nodes: {len(nodeTags)}, stress data: {len(data)}")
                # Try to handle mismatched data lengths
                if len(data) > len(nodeTags):
                    print("⚠️ Truncating excess stress data")
                    data = data[:len(nodeTags)]
                else:
                    print("⚠️ Padding missing stress data with zeros")
                    padding_needed = len(nodeTags) - len(data)
                    data.extend([[0.0] * len(data[0]) for _ in range(padding_needed)] if data else [[0.0] for _ in range(len(nodeTags))])
            
            svms = []
            for i, sig in enumerate(data):
                try:
                    if len(sig) == 9:
                        # Full tensor format (xx, xy, xz, yx, yy, yz, zx, zy, zz)
                        [xx, xy, xz, yx, yy, yz, zx, zy, zz] = sig
                        svm = np.sqrt(((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2 + 3 * (xy * xy + yz * yz + zx * zx))
                    elif len(sig) == 6:
                        # Symmetric tensor format (xx, yy, zz, xy, yz, zx)
                        [xx, yy, zz, xy, yz, zx] = sig
                        svm = np.sqrt(((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2 + 3 * (xy * xy + yz * yz + zx * zx))
                    elif len(sig) == 3:
                        # Principal stresses format (s1, s2, s3) or already computed von Mises
                        if numComp == 3:
                            # Assume this is already von Mises stress
                            svm = sig[0]  # Take first component as von Mises
                        else:
                            # Principal stresses - compute von Mises
                            [s1, s2, s3] = sig
                            svm = np.sqrt(((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2) / 2)
                    elif len(sig) == 1:
                        # Single value, likely already computed von Mises stress
                        svm = sig[0]
                    else:
                        print(f"⚠️ Unexpected stress data format at index {i}: {len(sig)} components (expected 1, 3, 6, or 9)")
                        svm = 0.0  # Default value
                    
                    svms.append(svm)
                except Exception as e:
                    print(f"⚠️ Error processing stress data at index {i}: {e}")
                    svms.append(0.0)  # Default value for problematic data
            
            svms = np.array(svms)
            
            # Ensure correct length
            if len(svms) != len(nodeTags):
                print(f"⚠️ Adjusting stress array length from {len(svms)} to {len(nodeTags)}")
                if len(svms) > len(nodeTags):
                    svms = svms[:len(nodeTags)]
                else:
                    svms = np.pad(svms, (0, len(nodeTags) - len(svms)), 'constant', constant_values=0.0)
            
            svmData = pd.DataFrame({'Von mises Stress': svms}, index=nodeTags)
            print(f"✅ Processed {len(svms)} stress values")
            
        except Exception as e:
            print(f"❌ Error processing stress tensor data: {e}")
            # Create dummy stress data to continue processing
            svms = np.zeros(len(nodeTags))
            svmData = pd.DataFrame({'Von mises Stress': svms}, index=nodeTags)
            print("⚠️ Using dummy stress data to continue processing")

        # Combine node and stress data
        nodeData.reset_index(drop=True, inplace=True)
        svmData.reset_index(drop=True, inplace=True)
        combinedData = pd.concat([nodeData, svmData], axis=1)

        # Process force vector data
        forces = np.zeros((len(nodeTags), 3))  # Default to zeros
        
        if force_view_tag is not None:
            try:
                print(f"🔍 DEBUG: Processing force data from view {force_view_tag}")
                dataType_force, tags_force, data_force, time_force, numComp_force = gmsh.view.getModelData(force_view_tag, 0)
                print(f"🔍 DEBUG: Force data - dataType: {dataType_force}, numComp: {numComp_force}, data length: {len(data_force)}")
                
                # Validate force data consistency
                if len(data_force) != len(nodeTags):
                    print(f"⚠️ WARNING: Force data length mismatch - nodes: {len(nodeTags)}, force data: {len(data_force)}")
                    # Try to handle mismatched data lengths
                    if len(data_force) > len(nodeTags):
                        print("⚠️ Truncating excess force data")
                        data_force = data_force[:len(nodeTags)]
                    else:
                        print("⚠️ Padding missing force data with zeros")
                        padding_needed = len(nodeTags) - len(data_force)
                        data_force.extend([[0.0, 0.0, 0.0] for _ in range(padding_needed)])
                
                forces = []
                for i, force in enumerate(data_force):
                    try:
                        if len(force) >= 3:
                            [fx, fy, fz] = force[:3]  # Take first 3 components
                            forces.append([fx, fy, fz])
                        elif len(force) == 1:
                            # Single component, assume it's magnitude
                            forces.append([force[0], 0.0, 0.0])
                        else:
                            print(f"⚠️ Unexpected force data format at index {i}: {len(force)} components (expected 1 or 3+)")
                            forces.append([0.0, 0.0, 0.0])
                    except Exception as e:
                        print(f"⚠️ Error processing force data at index {i}: {e}")
                        forces.append([0.0, 0.0, 0.0])
                
                forces = np.array(forces)
                
                # Ensure correct length
                if len(forces) != len(nodeTags):
                    print(f"⚠️ Adjusting force array length from {len(forces)} to {len(nodeTags)}")
                    if len(forces) > len(nodeTags):
                        forces = forces[:len(nodeTags)]
                    else:
                        padding_needed = len(nodeTags) - len(forces)
                        forces = np.vstack([forces, np.zeros((padding_needed, 3))])
                
                print(f"✅ Processed {len(forces)} force vectors")
                
            except Exception as e:
                print(f"❌ Error processing force vector data: {e}")
                forces = np.zeros((len(nodeTags), 3))
                print("⚠️ Using dummy force data to continue processing")
        else:
            print("⚠️ No force view available, using zero forces")
        
        combinedData = pd.concat([combinedData, pd.DataFrame(forces, columns=['Fx', 'Fy', 'Fz'])], axis=1)

        output_folder = folder_path

        # Export smooth stress tensor to CSV
        if export_smooth_stress:
            csv_file = os.path.join(output_folder, 'smooth_stress_tensor.csv')
            combinedData.to_csv(csv_file, index=False)
            print(f"✅ Smooth stress tensor exported: {os.path.basename(csv_file)}")

        # Export to VTK
        if export_vtk:
            print("🔍 DEBUG: Starting VTK export...")
            points = nodeCoords.reshape(-1, 3)
            elementTypes, elementTags, nodeTagsPerElement = gmsh.model.mesh.getElements()
            print("🔍 DEBUG: Got mesh elements from gmsh")
            cells = []
            for elementType, nodeTags in zip(elementTypes, nodeTagsPerElement):
                numNodesPerElement = gmsh.model.mesh.getElementProperties(elementType)[3]
                for element in nodeTags.reshape(-1, numNodesPerElement):
                    cells.append(np.insert(element - 1, 0, numNodesPerElement))
            cellsArray = np.concatenate(cells).astype(np.int_)
            print("🔍 DEBUG: Creating PyVista mesh...")
            mesh = pv.PolyData(points, cellsArray)
            print("🔍 DEBUG: PyVista mesh created successfully")
            mesh.point_data['Von mises Stress'] = svms
            mesh.point_data['Forces'] = forces
            vtk_file_path = os.path.join(output_folder, 'combined_data.vtk')
            print("🔍 DEBUG: Saving VTK file...")
            mesh.save(vtk_file_path)
            print(f"✅ VTK file exported: {os.path.basename(vtk_file_path)}")

        print("🔍 DEBUG: Finalizing gmsh...")
        
        # Complete cleanup before finalizing
        try:
            print("🔍 DEBUG: Performing complete gmsh cleanup...")
            
            # Clear all models with detailed logging
            model_list = gmsh.model.list()
            print(f"🔍 DEBUG: Found {len(model_list)} models to remove")
            for model_name in model_list:
                try:
                    gmsh.model.setCurrent(model_name)
                    gmsh.model.remove()
                    print(f"🔍 DEBUG: Removed model: {model_name}")
                except Exception as e:
                    print(f"🔍 DEBUG: Error removing model {model_name}: {e}")
            
            # Clear all views with detailed logging
            view_list = gmsh.view.getTags()
            print(f"🔍 DEBUG: Found {len(view_list)} views to remove")
            for view_tag in view_list:
                try:
                    gmsh.view.remove(view_tag)
                    print(f"🔍 DEBUG: Removed view: {view_tag}")
                except Exception as e:
                    print(f"🔍 DEBUG: Error removing view {view_tag}: {e}")
            
            # Clear any post-processing data
            try:
                gmsh.view.removeAllModels()
                print("🔍 DEBUG: Cleared all view models")
            except Exception as e:
                print(f"🔍 DEBUG: Error clearing view models: {e}")
            
            # Force clear any remaining mesh data
            try:
                gmsh.clear()
                print("🔍 DEBUG: Executed gmsh.clear()")
            except Exception as e:
                print(f"🔍 DEBUG: gmsh.clear() not available or failed: {e}")
            
            print("🔍 DEBUG: gmsh cleanup completed")
        except Exception as e:
            print(f"🔍 DEBUG: Warning during final gmsh cleanup: {e}")
        
        try:
            gmsh.finalize()
            print("🔍 DEBUG: gmsh finalized successfully")
        except Exception as e:
            print(f"🔍 DEBUG: Warning during gmsh finalization: {e}")

        # Export Von Mises stress summary
        if export_von_mises:
            export_von_mises_summary(selected_file, combinedData, output_folder)

        return True

    except Exception as e:
        print(f"❌ Error processing MSH files for {os.path.basename(selected_file)}: {e}")
        try:
            print("🔍 DEBUG: Cleaning up gmsh after error...")
            
            # Complete cleanup after error with detailed logging
            try:
                model_list = gmsh.model.list()
                print(f"🔍 DEBUG: Found {len(model_list)} models to clean after error")
                for model_name in model_list:
                    try:
                        gmsh.model.setCurrent(model_name)
                        gmsh.model.remove()
                        print(f"🔍 DEBUG: Removed model after error: {model_name}")
                    except Exception as model_err:
                        print(f"🔍 DEBUG: Error removing model {model_name}: {model_err}")
            except Exception as model_list_err:
                print(f"🔍 DEBUG: Error getting model list: {model_list_err}")
            
            try:
                view_list = gmsh.view.getTags()
                print(f"🔍 DEBUG: Found {len(view_list)} views to clean after error")
                for view_tag in view_list:
                    try:
                        gmsh.view.remove(view_tag)
                        print(f"🔍 DEBUG: Removed view after error: {view_tag}")
                    except Exception as view_err:
                        print(f"🔍 DEBUG: Error removing view {view_tag}: {view_err}")
            except Exception as view_list_err:
                print(f"🔍 DEBUG: Error getting view list: {view_list_err}")
            
            try:
                gmsh.view.removeAllModels()
                print("🔍 DEBUG: Cleared all view models after error")
            except Exception as remove_models_err:
                print(f"🔍 DEBUG: Error clearing view models: {remove_models_err}")
            
            try:
                gmsh.clear()
                print("🔍 DEBUG: Executed gmsh.clear() after error")
            except Exception as clear_err:
                print(f"🔍 DEBUG: gmsh.clear() not available or failed: {clear_err}")
            
            try:
                gmsh.finalize()
                print("🔍 DEBUG: gmsh cleanup after error completed")
            except Exception as finalize_err:
                print(f"🔍 DEBUG: Error during finalization: {finalize_err}")
                
        except Exception as cleanup_error:
            print(f"🔍 DEBUG: Error during cleanup: {cleanup_error}")
        return False

def export_von_mises_summary(selected_file, combinedData, output_folder):
    """Export Von Mises stress summary and analysis"""
    try:
        tolerance = 1e-4
        results_list = []
        
        # Basic statistics
        max_von_mises_stress = combinedData['Von mises Stress'].max()
        max_von_mises_stress_row = combinedData.loc[combinedData['Von mises Stress'].idxmax()]
        max_von_mises_stress_coords = max_von_mises_stress_row[['X', 'Y', 'Z']].values
        min_von_mises_stress = combinedData['Von mises Stress'].min()
        average_von_mises_stress = combinedData['Von mises Stress'].mean()
        
        results_list.append({
            'Value': 'Maximum',
            'Von mises Stress': max_von_mises_stress,
            'Coordinate X': max_von_mises_stress_coords[0],
            'Coordinate Y': max_von_mises_stress_coords[1],
            'Coordinate Z': max_von_mises_stress_coords[2]
        })
        results_list.append({'Value': 'Minimum', 'Von mises Stress': min_von_mises_stress})
        results_list.append({'Value': 'Average', 'Von mises Stress': average_von_mises_stress})

        # Average excluding 2% highest stresses
        combinedData2 = combinedData.sort_values(by='Von mises Stress', ascending=False)
        num_nodes = len(combinedData2)
        num_nodes_to_exclude = int(num_nodes * 0.02)
        combinedData2 = combinedData2.iloc[num_nodes_to_exclude:]
        average_von_mises_stress2 = combinedData2['Von mises Stress'].mean()
        results_list.append({'Value': 'Average (excluding 2% highest)', 'Von mises Stress': average_von_mises_stress2})

        # Process areas of interest from Python file
        found_areas_of_interest = False
        area_von_mises_stress = {}
        
        if os.path.exists(selected_file):
            with open(selected_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if found_areas_of_interest and line.startswith("#"):
                        try:
                            name, coordinates_str = line.strip("#").strip().split(":")
                            coordinates_list = json.loads(coordinates_str)
                            von_mises_stresses = []
                            for coord_group in coordinates_list:
                                coordinates = [float(str(coord).strip()) for coord in coord_group]
                                x, y, z = coordinates
                                matching_rows = combinedData[
                                    (abs(combinedData['X'] - x) < tolerance) &
                                    (abs(combinedData['Y'] - y) < tolerance) &
                                    (abs(combinedData['Z'] - z) < tolerance)
                                ]
                                if not matching_rows.empty:
                                    von_mises_stress = matching_rows['Von mises Stress'].mean()
                                    von_mises_stresses.append(von_mises_stress)
                                else:
                                    print(f"   ⚠️  Coordinates ({x:.2f}, {y:.2f}, {z:.2f}) not found in data")
                            if von_mises_stresses:
                                area_von_mises_stress[name.strip()] = (np.mean(von_mises_stresses), len(von_mises_stresses))
                        except Exception as e:
                            print(f"   ⚠️  Error processing coordinates: {e}")
                    elif "# Areas of interest" in line:
                        found_areas_of_interest = True
        
        # Add area results
        for name, data in area_von_mises_stress.items():
            average_von_mises_stress, num_elements = data
            results_list.append({
                'Value': name,
                'Von mises Stress': average_von_mises_stress,
                'Coordinate X': None,
                'Coordinate Y': None,
                'Coordinate Z': None,
                'Number of nodes': num_elements
            })

        # Process fixations (if available)
        process_fixations_data(selected_file, combinedData, results_list, tolerance)

        # Save results
        results_df = pd.DataFrame(results_list)
        results_csv = os.path.join(output_folder, 'von_mises_stress_results.csv')
        results_df.to_csv(results_csv, index=False)
        
        print(f"✅ Von Mises stress summary exported: {os.path.basename(results_csv)}")
        print(f"   📊 Max stress: {max_von_mises_stress:.2f}")
        print(f"   📊 Min stress: {min_von_mises_stress:.2f}")
        print(f"   📊 Avg stress: {average_von_mises_stress:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error creating Von Mises summary: {e}")

def process_fixations_data(selected_file, combinedData, results_list, tolerance):
    """Process fixation data from the Python file"""
    try:
        if not os.path.exists(selected_file):
            return
            
        fixations_found = False
        accumulating = False
        json_string = ""
        
        with open(selected_file, 'r', encoding='utf-8') as f:
            previous_line = ''
            for line in f:
                if 'p[' in line and 'fixations' in line:
                    accumulating = True
                    json_string = '{"fixations":' + line.split('fixations')[1].split('] = ')[1].strip()
                elif accumulating:
                    if line.strip().startswith('p') and previous_line.strip().endswith(']'):
                        json_string += previous_line.strip() + "}"
                        json_string = json_string[:-3] + "]}"

                        accumulating = False
                        try:
                            fixations = json.loads(json_string.replace("'", '"'))
                            fixations_found = True
                            for fixation in fixations['fixations']:
                                x, y, z = fixation['nodes'][0]
                                matching_rows = combinedData[
                                    (abs(combinedData['X'] - x) < tolerance) &
                                    (abs(combinedData['Y'] - y) < tolerance) &
                                    (abs(combinedData['Z'] - z) < tolerance)
                                ]
                                if not matching_rows.empty:
                                    row = matching_rows.iloc[0]
                                    fx, fy, fz = row[['Fx', 'Fy', 'Fz']].values
                                    results_list.append({
                                        'Value': fixation['name'],
                                        'Von mises Stress': None,
                                        'Coordinate X': x,
                                        'Coordinate Y': y,
                                        'Coordinate Z': z,
                                        'Fx': fx,
                                        'Fy': fy,
                                        'Fz': fz
                                    })
                                else:
                                    print(f"   ⚠️  Fixation node ({x:.2f}, {y:.2f}, {z:.2f}) not found")
                        except json.JSONDecodeError as e:
                            print(f"   ⚠️  Error decoding fixations JSON: {e}")
                        json_string = ""
                    else:
                        json_string += line.strip()
                        previous_line = line
        
        if not fixations_found:
            print("   ℹ️  No fixations found in Python file")
            
    except Exception as e:
        print(f"   ⚠️  Error processing fixations: {e}")

def rename_workspace_folder(python_file):
    """Rename the workspace folder to match the Python file name"""
    try:
        base_name = os.path.splitext(os.path.basename(python_file))[0]
        # Get the directory where the executable is running from
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(script_dir, "workspace")
        
        if not os.path.exists(workspace_dir):
            print(f"⚠️  Workspace directory not found: {workspace_dir}")
            return False
        
        # Find folders that might be the output from this python file
        target_folder = None
        longest_match = 0
        
        for folder_name in os.listdir(workspace_dir):
            folder_path = os.path.join(workspace_dir, folder_name)
            if os.path.isdir(folder_path):
                # Look for folders that contain parts of the base name
                # or where the base name contains parts of the folder name
                if base_name.lower() in folder_name.lower():
                    match_length = len(base_name)
                    if match_length > longest_match:
                        longest_match = match_length
                        target_folder = folder_path
                elif any(word in folder_name.lower() for word in base_name.lower().split('_') if len(word) > 3):
                    # Check for word matches in underscored names
                    words_matched = sum(1 for word in base_name.lower().split('_') if len(word) > 3 and word in folder_name.lower())
                    if words_matched > longest_match:
                        longest_match = words_matched
                        target_folder = folder_path
        
        if target_folder:
            expected_folder_name = base_name
            expected_folder_path = os.path.join(workspace_dir, expected_folder_name)
            
            # Only rename if it's not already correctly named
            if os.path.basename(target_folder) != expected_folder_name:
                # If target already exists, remove it first
                if os.path.exists(expected_folder_path):
                    print(f"🗑️  Removing existing folder: {expected_folder_path}")
                    import shutil
                    shutil.rmtree(expected_folder_path)
                
                print(f"📁 Renaming workspace folder:")
                print(f"   From: {os.path.basename(target_folder)}")
                print(f"   To: {expected_folder_name}")
                
                os.rename(target_folder, expected_folder_path)
                print(f"✅ Workspace folder renamed successfully")
                return True
            else:
                print(f"✅ Workspace folder already has correct name: {expected_folder_name}")
                return True
        else:
            print(f"⚠️  Could not find workspace folder for: {base_name}")
            # List available folders for debugging
            print("📂 Available workspace folders:")
            for folder_name in os.listdir(workspace_dir):
                folder_path = os.path.join(workspace_dir, folder_name)
                if os.path.isdir(folder_path):
                    print(f"   📂 {folder_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error renaming workspace folder for {os.path.basename(python_file)}: {e}")
        return False

# Main application entry point
if __name__ == "__main__":
    try:
        # Update initial status
        update_telegram_status_label()
        
        # Start the GUI main loop
        print("Starting MSH file converter GUI...")
        app.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        # Keep console open for debugging
        input("Press Enter to exit...")