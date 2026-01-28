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
import numpy as np
import pandas as pd

import re

# Try to import optional dependencies for MSH processing
try:
    import gmsh
    import pyvista as pv
    from pyvista import _vtk as vtk
    MSH_PROCESSING_AVAILABLE = True
    print("✅ MSH processing libraries available (gmsh, pyvista)")
except ImportError as e:
    MSH_PROCESSING_AVAILABLE = False
    print(f"⚠️  MSH processing libraries not available: {e}")
    print("   Install with: pip install gmsh pyvista")
    print("   MSH to CSV/VTK conversion will be disabled")

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
        if MSH_PROCESSING_AVAILABLE:
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
            # Try to extract workspace path from Fossils stdout if available and pass as hint
            workspace_hint = None
            try:
                # Capture lines like: workspace = /path/to/workspace
                # We need to ensure we are searching in the stdout we just captured
                if stdout:
                    m = re.search(r"^\s*workspace\s*[:=]\s*(.+)$", stdout, flags=re.MULTILINE | re.IGNORECASE)
                    if m:
                        workspace_hint = m.group(1).strip().strip('"\'')
                        # remove any trailing text after a space (in case line contains extra words)
                        # Actually in the log provided: "workspace = /path/to/workspace" seems clean, 
                        # but let's be careful not to split paths with spaces if they are valid.
                        # However, Fossils log output might not quote paths.
                        # The user provided log: 
                        # workspace = /home/miguel/.../ossils_fossils_dist_fossils__internal_models_others_dolicorhynchops_dolicorhynchops_10k (copy)
                        # It contains spaces at the end "(copy)". So splitting by space might be dangerous if the path has spaces.
                        # We should trust the capture group until the end of line.
                        workspace_hint = os.path.normpath(workspace_hint)
                        print(f"🔎 Detected workspace path in Fossils output: {workspace_hint}")
            except Exception as e:
                print(f"⚠️ Error parsing workspace hint: {e}")
                workspace_hint = None

            rename_success, renamed_workspace_path = rename_workspace_folder(file, workspace_hint=workspace_hint)
            if rename_success:
                print(f"✅ Workspace folder rename completed for: {os.path.basename(file)}")
                # Update workspace_hint to the renamed path
                if renamed_workspace_path:
                    workspace_hint = renamed_workspace_path
            else:
                print(f"⚠️  Workspace folder rename failed for: {os.path.basename(file)}")
            
            # Process MSH files automatically if libraries are available and Export VTK is enabled
            should_auto_convert = False
            try:
                # We need to access the checkbox variable. 
                # Since we are in a thread, direct access might be unsafe but `get()` on BooleanVar 
                # is generally thread-safe in CPython for reading (Tcl is thread-specific but Tkinter wraps it).
                # However, safe approach is usually `app.after` with a queue, but here we need the value now.
                # Given the context of this script, reading the variable is the standard way.
                # Note: `export_vtk_var` is the unified toggle.
                should_auto_convert = bool(export_vtk_var.get())
            except Exception:
                # Fallback if variable access fails
                should_auto_convert = True # Default to True or False? 
                # Ideally default to what was configured. Let's assume True if we can't read it?
                # Or False to be safe.
                should_auto_convert = True

            if MSH_PROCESSING_AVAILABLE and should_auto_convert:
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
                        export_vtk=export_vtk,
                        workspace_hint=workspace_hint
                    )
                    
                    if msh_success:
                        print(f"✅ MSH processing completed for: {os.path.basename(file)}")
                    else:
                        print(f"⚠️ MSH processing failed for: {os.path.basename(file)}")
                        
                except Exception as e:
                    print(f"❌ Error during MSH processing for {os.path.basename(file)}: {e}")
            else:
                if not should_auto_convert:
                    print(f"⚪ Auto-convert disabled (Export VTK unchecked); skipping MSH processing for: {os.path.basename(file)}")
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
                if MSH_PROCESSING_AVAILABLE:
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
    # Use export_vtk as auto-convert-results flag too since they are merged in logic
    if export_vtk_var.get():
        pass 
             
    # Cleanup option: Convert_to_csv supports --no-cleanup to prevent deletion
    if not cleanup_var.get():
        export_options.append("--no-cleanup")

    for file in selected_files:
        threading.Thread(target=run_conversion, args=(folder_path, file, export_options, on_conversion_complete)).start()

def run_conversion(folder_path, file, export_options, callback):

    # Determinar la ubicación base según si estamos ejecutando desde un ejecutable o un script
    if getattr(sys, 'frozen', False):

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

# Cleanup option: Cleanup folder after processing
cleanup_var = tk.BooleanVar(value=True)
cleanup_check = ctk.CTkCheckBox(convert_section, text="Cleanup folder after processing", variable=cleanup_var)
cleanup_check.select()
cleanup_check.pack(pady=5)
    
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

def find_msh_files(python_file, workspace_hint=None):
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
    
    # 0. Priority: If workspace_hint is provided and exists, use it.
    if workspace_hint and os.path.isdir(workspace_hint):
        print(f"🔎 Using workspace hint: {workspace_hint}")
        possible_locations.append(workspace_hint)
        # Also add parent + base_name, in case the hint was the original name before rename
        # But if rename_workspace_folder succeeded, the folder is now 'base_name' in the same parent dir.
        possible_locations.append(os.path.join(os.path.dirname(workspace_hint), base_name))

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
    
    # 5. Also search in repo_root/workspace
    repo_root = os.path.abspath(os.path.join(script_dir, '..'))
    workspace_dirs.append(os.path.join(repo_root, 'workspace'))
    
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
        strain_tensor_file = os.path.join(folder_path, 'smooth_strain_tensor.msh')
        force_vector_file = os.path.join(folder_path, 'force_vector.msh')

        # Check if all required files exist
        files_exist = [
            os.path.exists(mesh_file),
            os.path.exists(stress_tensor_file),
            os.path.exists(force_vector_file)
        ]
        
        strain_exists = os.path.exists(strain_tensor_file)
        
        print(f"      📄 mesh.msh: {'✅' if files_exist[0] else '❌'}")
        print(f"      📄 smooth_stress_tensor.msh: {'✅' if files_exist[1] else '❌'}")
        print(f"      📄 smooth_strain_tensor.msh: {'✅' if strain_exists else '❌'}")
        print(f"      📄 force_vector.msh: {'✅' if files_exist[2] else '❌'}")

        if all(files_exist):
            print(f"   ✅ Found MSH files in: {folder_path}")
            return mesh_file, stress_tensor_file, force_vector_file, strain_tensor_file if strain_exists else None
    
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
    
    return None, None, None, None

def process_fossils_output(selected_file, export_von_mises=True, export_smooth_stress=True, export_vtk=True, workspace_hint=None):
    """Process Fossils output MSH files and convert them to CSV/VTK by calling Convert_to_csv.py"""
    
    # We will invoke Convert_to_csv.py as a subprocess to keep logic separated.
    # We just need to construct the command.
    
    print(f"🔄 Delegating MSH processing for {os.path.basename(selected_file)} to Convert_to_csv.py...")
    
    # Locate Convert_to_csv.py
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    script_path = os.path.join(base_dir, 'Convert_to_csv.py')
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Convert_to_csv.py not found at {script_path}")
        return False
        
    # Construct arguments
    # Convert_to_csv.py arguments: directory files... [--flags]
    # It expects: directory file1 file2 ...
    directory = os.path.dirname(selected_file)
    filename = os.path.basename(selected_file)
    
    
    cmd = [sys.executable, script_path, directory, filename]
    
    if export_von_mises:
        cmd.append("--export-von-mises")
    if export_smooth_stress:
        cmd.append("--export-smooth-stress")
    if export_vtk:
        cmd.append("--export-vtk")
    
    # Pass workspace_hint if available
    if workspace_hint:
        cmd.extend(["--workspace-dir", workspace_hint])
        
    try:
        # Run the subprocess
        print(f"🔍 DEBUG: Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("🔍 DEBUG: Convert_to_csv output:")
        print(result.stdout)
        
        if result.stderr:
            print("🔍 DEBUG: Convert_to_csv stderr:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ Convert_to_csv completed successfully")
            return True
        else:
            print(f"❌ Convert_to_csv failed with code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run Convert_to_csv.py: {e}")
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

def rename_workspace_folder(python_file, workspace_hint=None):
    """Rename the workspace folder to match the Python file name
    
    Returns:
        tuple: (success: bool, renamed_path: str or None) where renamed_path is the final workspace path
    """
    try:
        base_name = os.path.splitext(os.path.basename(python_file))[0]
        # Get the directory where the executable is running from
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        # Candidate workspace directories to search
        workspace_candidates = []

        # 1) workspace folder next to this script (msh2vtk/workspace)
        workspace_candidates.append(os.path.join(script_dir, "workspace"))

        # 2) workspace folder in the repo root (parent of script_dir)
        repo_root = os.path.abspath(os.path.join(script_dir, '..'))
        workspace_candidates.append(os.path.join(repo_root, 'workspace'))

        # 3) workspace folder next to the python file's directory
        python_parent = os.path.dirname(python_file)
        workspace_candidates.append(os.path.join(python_parent, 'workspace'))

        # 4) if Fossils printed an explicit workspace path, include its parent
        if workspace_hint:
            # If hint is a folder path that already contains the run folder, use it directly
            # We don't just search the parent, we consider the hint itself might be the target
            workspace_candidates.append(os.path.dirname(workspace_hint))

        # Normalize and deduplicate
        seen = set()
        workspace_candidates_norm = []
        for p in workspace_candidates:
            try:
                pn = os.path.normpath(p)
            except Exception:
                continue
            if pn not in seen:
                seen.add(pn)
                workspace_candidates_norm.append(pn)

        # Find folders that might be the output from this python file
        target_folder = None
        longest_match = 0

        # If the Fossils stdout contained an explicit workspace path and it exists, prefer it
        if workspace_hint and os.path.isdir(workspace_hint):
            # Verify if it seems related
            if base_name.lower() in os.path.basename(workspace_hint).lower() or \
               base_name.lower() in workspace_hint.lower() or \
               any(word in os.path.basename(workspace_hint).lower() for word in base_name.lower().split('_') if len(word) > 3):
                target_folder = workspace_hint
                print(f"🔎 Using workspace from Fossils output: {target_folder}")

        # Otherwise scan candidate workspace directories
        if not target_folder:
            for workspace_dir in workspace_candidates_norm:
                if not os.path.exists(workspace_dir):
                    # skip non-existing candidate
                    continue
                try:
                    for folder_name in os.listdir(workspace_dir):
                        folder_path = os.path.join(workspace_dir, folder_name)
                        if os.path.isdir(folder_path):
                            # Look for folders that contain parts of the base name
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
                except Exception as e:
                    print(f"   ⚠️  Error scanning workspace directory {workspace_dir}: {e}")
        
        if target_folder:
            expected_folder_name = base_name
            expected_folder_path = os.path.join(os.path.dirname(target_folder), expected_folder_name)
            
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
                return True, expected_folder_path
            else:
                print(f"✅ Workspace folder already has correct name: {expected_folder_name}")
                return True, expected_folder_path
        else:
            print(f"⚠️  Could not find workspace folder for: {base_name}")
            # List available folders for debugging from all candidate workspace locations
            print("📂 Available workspace folders (scanned locations):")
            for candidate in workspace_candidates_norm:
                try:
                    if os.path.exists(candidate):
                        print(f"   Location: {candidate}")
                        for folder_name in os.listdir(candidate):
                            folder_path = os.path.join(candidate, folder_name)
                            if os.path.isdir(folder_path):
                                print(f"      📂 {folder_name}")
                except Exception as e:
                    print(f"   ⚠️  Error listing candidate {candidate}: {e}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error renaming workspace folder for {os.path.basename(python_file)}: {e}")
        return False, None
        
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