# Model Context Protocol

This project provides MCP (Model Context Protocol) servers that support integration with various communication channels, including Telegram, Gmail, and Google Drive.

## Features

### mcp_server_4.py (Telegram Server)
- Send text messages to Telegram chats
- Send photos to Telegram chats
- Send documents/files to Telegram chats
- Receive messages via Telegram webhook
- Secure credential management for Telegram bots
- Web search functionality via DuckDuckGo

### mcp_server_5.py (Google Services Server)
- Send emails via Gmail (with HTML content and attachments)
- Manage files in Google Drive (create, upload, etc.)
- Secure credential management for Google services

## Prerequisites

Make sure you have the following requirements installed:

```bash
pip install python-telegram-bot fastapi uvicorn httpx beautifulsoup4 aiohttp google-auth google-auth-oauthlib google-api-python-client
```

## Configuration

### Telegram Bot Setup
1. Create a Telegram bot using BotFather on Telegram
2. Get your bot token
3. Start a chat with your bot to get the chat ID

### Google Services Setup
1. Create a Google Cloud project
2. Enable Gmail and Google Drive APIs
3. Set up OAuth 2.0 credentials
4. For Gmail, create an App Password in your Google Account security settings

## Running the Servers

### Option 1: Running Individual Servers

#### Telegram Server

```bash
uvicorn mcp_server_4:app --reload
```

The server will run at `http://localhost:8000`

#### Google Services Server

```bash
uvicorn mcp_server_5:app --reload --port 8001
```

The server will run at `http://localhost:8001`

### Option 2: Using the Integrated Client (Recommended)

The `client.py` script provides an integrated solution that:
- Receives messages from Telegram using long polling (no webhook required)
- Automatically starts the Google Services server
- Processes messages and routes them to appropriate services
- Provides a simple API for additional integrations

To run the client:

```bash
python client.py
```

The client will:
1. Check if the Telegram server is running (it must be started separately)
2. Start the Google Services server automatically
3. Connect to Telegram via long polling to receive messages in real-time
4. Also run a FastAPI server on port 5000 for additional integrations

**Note:** The Telegram server (mcp_server_4.py) must still be running and properly configured with your bot token.

## Setting Up Credentials

Before using any services, you need to set up credentials. Use the following tools:

### For Telegram Server

```
Set Telegram Bot Token:
POST /set_credentials?service=telegram&key=bot_token&value=YOUR_BOT_TOKEN

Set Default Chat ID (optional):
POST /set_credentials?service=telegram&key=default_chat_id&value=YOUR_CHAT_ID
```

Note: We're using query parameters instead of a JSON body for simplicity.

### For Google Services Server

```
Set Gmail Credentials:
POST /api/mcp/tool/set_google_credentials
{
  "service": "gmail",
  "key": "email",
  "value": "your.email@gmail.com"
}

POST /api/mcp/tool/set_google_credentials
{
  "service": "gmail",
  "key": "app_password",
  "value": "YOUR_APP_PASSWORD"
}

Set Google Drive Credentials:
POST /api/mcp/tool/set_google_credentials
{
  "service": "gdrive",
  "key": "client_id",
  "value": "YOUR_CLIENT_ID"
}

POST /api/mcp/tool/set_google_credentials
{
  "service": "gdrive",
  "key": "client_secret",
  "value": "YOUR_CLIENT_SECRET"
}
```

## Usage Examples

### Sending a Telegram Message

You'll need to use the correct path to the mounted MCP tools. Since the MCP app is mounted at the root, the path is simply `/tool/[tool_name]`:

```
POST /tool/send_telegram_message
{
  "message": "Hello, this is a test message!",
  "chat_id": "YOUR_CHAT_ID",  // Optional if default is set
  "parse_mode": "HTML",       // Optional: "HTML", "MarkdownV2", or null for auto-detect
  "disable_notification": false // Optional
}
```

### Sending a Telegram Photo

```
POST /tool/send_telegram_photo
{
  "photo_path": "/path/to/your/photo.jpg",
  "caption": "Check out this photo!",
  "chat_id": "YOUR_CHAT_ID",  // Optional if default is set
  "disable_notification": false // Optional
}
```

### Sending a Telegram Document/File

```
POST /tool/send_telegram_document
{
  "document_path": "/path/to/your/document.pdf",
  "caption": "Here's the document you requested",
  "chat_id": "YOUR_CHAT_ID"  // Optional if default is set
}
```

### Telegram Long Polling (No Webhook Required)

With the updated client.py, your bot will now use long polling to receive messages from Telegram. This means:

1. No webhook configuration is needed
2. No public URL is required
3. Works entirely behind firewalls and NAT

To use this method:

1. Set up your Telegram bot token in the server
2. Start both the server and client
3. The client automatically connects to Telegram's API to receive messages

### Using the Client with Telegram Messages

The client.py script processes special message formats from Telegram to trigger actions:

#### Sending Emails via Telegram

To send an email from Telegram, use this format:
```
email:recipient@example.com|Subject Line|Email body content here
```

#### Creating Google Docs via Telegram

To create a Google Doc from Telegram, use this format:
```
upload:Document Name|Document content goes here
```

The client will process these commands and use the Google Services server to perform the requested actions.

### Sending an Email via Gmail

```
POST /api/mcp/tool/send_gmail_message
{
  "to": "recipient@example.com",
  "subject": "Test Email",
  "body": "<h1>Hello!</h1><p>This is a test email from our MCP server.</p>",
  "attachments": ["/path/to/attachment.pdf"]  // Optional
}
```

### Uploading a File to Google Drive

```
POST /api/mcp/tool/manage_gdrive_file
{
  "name": "My Document",
  "file_path": "/path/to/your/file.pdf"
}
```

## Security Considerations

- Credentials are stored in a local `credentials.json` file. Make sure this file is secure and not included in version control.
- For production use, consider implementing more robust security measures.
- The first time you use Google Drive, it will prompt you to authenticate via a browser.

## Troubleshooting

- If you experience issues with Telegram, verify your bot token and chat ID
- For Gmail issues, ensure you're using an App Password if you have 2-factor authentication
- For Google Drive issues, you may need to re-authenticate if the token expires

## License

This project is licensed under the MIT License - see the LICENSE file for details.


I'll help you with setting up a Telegram bot for this project. Here's a step-by-step guide:

  1. Create a Telegram Bot using BotFather:
    - Open Telegram and search for "@BotFather"
    - Start a chat with BotFather by clicking "Start"
    - Send the command /newbot
    - Follow the prompts to name your bot
    - Choose a username for your bot (must end with "bot")
    - BotFather will give you a token like 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
  2. Set Your Bot Token in the Server:
    - Start the Telegram server:
  uvicorn mcp_server_4:app --reload
    - Set the bot token using this API call:
  POST http://localhost:8000/set_credentials?service=telegram&key=bot_token&value=YOUR_BOT_TOKEN
  
  3. Get Your Chat ID:
    - Start a conversation with your bot by searching its username
    - Send any message to your bot
    - Use this link to get chat IDs (replace with your token):
  https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
    - Look for the "chat" object and note the "id" value
    - Set this as default chat ID (optional):
  POST http://localhost:8000/set_credentials?service=telegram&key=default_chat_id&value=YOUR_CHAT_ID
  4. Set Up Webhook (for receiving messages):
    - You need a public URL (use ngrok for testing)
    - Start ngrok: ngrok http 5000
    - Take the HTTPS URL from ngrok (e.g., https://a1b2c3d4.ngrok.io)
    - Set the webhook:
  POST http://localhost:8000/set_webhook
  {
    "webhook_url": "https://a1b2c3d4.ngrok.io",
    "secret_token": "YOUR_SECRET_TOKEN"
  }
  5. Start the Client:
  python client.py
  6. Test Your Bot:
    - Send a message to your bot on Telegram
    - Try special commands:
        - email:recipient@example.com|Subject|Body
      - upload:Document Name|Document content

  Your bot should now receive messages and respond appropriately, integrating with both Telegram and Google services.