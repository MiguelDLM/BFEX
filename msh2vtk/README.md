# MSH2VTK - File Converter with Telegram Notifications

A GUI application for converting MSH files and running Fossils analysis with optional Telegram notifications.

## Features

- **File Conversion**: Convert MSH files to various formats (CSV, VTK)
- **Fossils Integration**: Execute Fossils analysis directly from the interface
- **Telegram Notifications**: Get real-time updates on your phone about analysis progress
- **Batch Processing**: Process multiple files simultaneously
- **Progress Tracking**: Visual progress bar and file status indicators

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Telegram Notifications Setup

To receive notifications on your phone during long-running analyses:

### 1. Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Save the **Bot Token** you receive

### 2. Get Your Chat ID
1. Send a message to your newly created bot
2. Open this URL in your browser (replace `<YOUR_BOT_TOKEN>` with your actual token):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Look for the `"id"` field inside the `"chat"` object - this is your **Chat ID**

### 3. Configure in MSH2VTK
1. Click the "⚙️ Settings" button in the application
2. Enter your Bot Token and Chat ID
3. Click "Test & Save" to verify the configuration
4. You should receive a test message on Telegram

## Usage

### Basic File Conversion
1. Click "Browse" to select a folder containing Python files
2. Select the files you want to convert using the checkboxes
3. Choose export options (CSV, VTK, etc.)
4. Click "Convert" to start the process

### Fossils Analysis
1. Set the path to your Fossils executable using "Browse"
2. Select the files you want to analyze
3. Click "Execute Fossils"
4. Monitor progress in the log area

### Telegram Notifications
When enabled, you'll receive notifications for:
- ✅ **Analysis Start**: When batch processing begins
- 📊 **Progress Updates**: Individual file completions
- 🎉 **Completion Summary**: When all files are processed
- ❌ **Error Alerts**: If any files fail to process
- ⏰ **Timeout Warnings**: If analysis takes too long

## File Structure

```
msh2vtk/
├── main.py              # Main GUI application
├── Convert_to_csv.py    # Conversion script
├── requirements.txt     # Python dependencies
└── telegram_config.json # Telegram configuration (auto-generated)
```

## Troubleshooting

### Telegram Issues
- **Test connection fails**: Verify your Bot Token and Chat ID are correct
- **No notifications received**: Check if your bot is properly configured and you've sent it at least one message
- **Connection timeout**: Check your internet connection

### File Conversion Issues
- **No files found**: Ensure your Python files contain the expected structure
- **Conversion fails**: Check the log output for specific error messages
- **Permission errors**: Ensure you have write permissions in the target directory

## Configuration Files

### telegram_config.json
This file is automatically created when you configure Telegram notifications:
```json
{
  "bot_token": "your_bot_token_here",
  "chat_id": "your_chat_id_here"
}
```

You can manually edit this file or delete it to disable notifications.

## Dependencies

- `customtkinter`: Modern GUI framework
- `requests`: For Telegram API communication
- `tkinter`: Built-in Python GUI library

## Building a Lightweight Executable

The project includes PyInstaller spec files for Windows and Linux
(located in this folder). To generate a smaller standalone binary:

1. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. Build using the spec file for your platform with the `--clean`,
   `--onefile` and `--strip` options:

   ```bash
   pyinstaller --clean --onefile --strip main_linux.spec    # on Linux
   pyinstaller --clean --onefile --strip main_windows.spec  # on Windows
   ```

These spec files list only the required libraries (numpy, pandas, gmsh,
pyvista, requests and the GUI modules). Adjust them if you remove or add
dependencies to keep the generated executable as small as possible.

## License

This project is part of the BFEX (Biomechanical Finite Element Analysis) suite.
