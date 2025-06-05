# MSH2VTK - Configuration Guide

## Telegram Notifications Setup

MSH2VTK now supports Telegram notifications to keep you informed about the progress of your file conversions and Fossils analyses.

### Prerequisites

1. **Create a Telegram Bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Save the **Bot Token** provided by BotFather

2. **Get your Chat ID:**
   - Send a message to your newly created bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for the `"id"` value in the `"chat"` field
   - This is your **Chat ID**

### Configuration Steps

1. **Open Settings:**
   - Launch MSH2VTK
   - Click the "⚙️ Settings" button in the top-left corner

2. **Configure Fossils Path:**
   - Go to the "Fossils" tab (first tab)
   - Click "📁 Browse" to select your Fossils executable
   - Click "💾 Save" to save the path

3. **Configure Telegram:**
   - Go to the "Telegram" tab
   - Enter your **Bot Token** in the first field
   - Enter your **Chat ID** in the second field
   - Click "💾 Save" to save the configuration
   - Click "🧪 Test" to test the connection

### Features

#### Telegram Notifications
When enabled, you'll receive notifications for:
- **Start of batch operations** with file count and timestamp
- **Individual file completions** with progress updates
- **Error notifications** if files fail to process
- **Final summary** with success/failure statistics

#### Notification Types
- 🚀 **Start notifications**: When beginning file conversions or Fossils analyses
- ✅ **Success notifications**: When individual files complete successfully
- ❌ **Error notifications**: When files fail to process
- 📈 **Progress notifications**: Periodic updates during batch operations
- 🎉 **Completion notifications**: Final summary when all files are processed

### Testing

#### Using the GUI
- Use the "🧪 Test" button in settings to send a test message
- Use "💾 Save" to save configuration separately

#### Using the Test Script
Run the standalone test script:
```bash
python3 test_telegram.py
```

This script will:
- Load your saved configuration
- Test the connection
- Allow you to send custom test messages

### Troubleshooting

#### Common Issues
1. **"Connection test failed"**
   - Verify your bot token is correct
   - Ensure you've sent at least one message to your bot
   - Check your internet connection

2. **"Chat ID not found"**
   - Make sure you've sent a message to your bot first
   - Visit the getUpdates URL to find your correct Chat ID
   - Ensure the Chat ID is a number (can be negative)

3. **"Telegram: DISABLED" status**
   - Check that both bot token and chat ID are configured
   - Try saving and testing separately to re-enable

#### Status Indicators
- 📱 **Telegram: ENABLED** (green) - Configuration is active
- 📱 **Telegram: DISABLED** (red) - No configuration or disabled

### Security Notes

- Your bot token and chat ID are stored locally in `telegram_config.json`
- Never share your bot token publicly
- The configuration file is excluded from version control
- You can disable notifications at any time using the "🚫 Disable" button

### Advanced Usage

#### Silent Notifications
Some notifications (like progress updates) are sent with silent mode enabled to avoid constant phone buzzing during long batch operations.

#### Custom Messages
You can use the test script to send custom messages and verify your bot is working correctly.

## Fossils Configuration

### Path Setup
1. Go to Settings → Fossils tab (first tab)
2. Click "📁 Browse" to select your Fossils executable
3. Click "💾 Save" to apply the configuration

### Supported Platforms
- **Linux**: Use the Fossils binary for Linux
- **Windows**: Use the Fossils .exe file

### Testing Fossils
The path is saved directly when you select it using the browse button. You can verify the executable is working by trying to run a Fossils analysis.
