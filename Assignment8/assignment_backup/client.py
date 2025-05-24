#!/usr/bin/env python3
# client.py

import asyncio
import aiohttp
import json
import os
import signal
import subprocess
import sys
import time
from typing import Dict, Any, Optional, List

# Import Telethon library for Telegram API
from telethon import TelegramClient, events

# URLs for the MCP servers
TELEGRAM_SERVER_URL = "http://localhost:8000"
GOOGLE_SERVER_URL = "http://localhost:8001"

# Global variable to store Google server process
google_process = None
telegram_client = None

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")


async def start_google_server():
    """Start the Google Services server as a subprocess."""
    global google_process
    
    log("STARTUP", "Starting Google Services server...")
    try:
        # Start the Google Services server
        cmd = ["uvicorn", "mcp_server_5:app", "--port", "8001"]
        google_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for _ in range(30):  # Wait up to 30 seconds
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{GOOGLE_SERVER_URL}/test") as response:
                        if response.status == 200:
                            log("STARTUP", "Google Services server started successfully")
                            return True
            except aiohttp.ClientError:
                await asyncio.sleep(1)
        
        log("ERROR", "Failed to start Google Services server")
        return False
    
    except Exception as e:
        log("ERROR", f"Error starting Google Services server: {e}")
        return False


async def check_telegram_server():
    """Check if the Telegram server is running."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{TELEGRAM_SERVER_URL}/test") as response:
                if response.status == 200:
                    return True
                return False
    except:
        return False


async def get_telegram_credentials():
    """Get Telegram credentials from the server."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{TELEGRAM_SERVER_URL}/get_telegram_credentials") as response:
                if response.status == 200:
                    return await response.json()
                log("ERROR", f"Failed to get Telegram credentials: {await response.text()}")
                return None
    except Exception as e:
        log("ERROR", f"Error getting Telegram credentials: {e}")
        return None


async def send_gmail(to: str, subject: str, body: str):
    """Send an email using the Google Services server."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "to": to,
                "subject": subject,
                "body": body
            }
            async with session.post(
                f"{GOOGLE_SERVER_URL}/tool/send_gmail_message",
                json=payload
            ) as response:
                if response.status == 200:
                    log("GMAIL", f"Sent email to {to}")
                    return True
                else:
                    log("ERROR", f"Failed to send email: {await response.text()}")
                    return False
    except Exception as e:
        log("ERROR", f"Error sending Gmail: {e}")
        return False


async def create_google_doc(name: str, content: str):
    """Create a Google Doc using the Google Services server."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "name": name,
                "content": content
            }
            async with session.post(
                f"{GOOGLE_SERVER_URL}/tool/manage_gdrive_file",
                json=payload
            ) as response:
                if response.status == 200:
                    log("GDRIVE", f"Created document: {name}")
                    return True
                else:
                    log("ERROR", f"Failed to create document: {await response.text()}")
                    return False
    except Exception as e:
        log("ERROR", f"Error creating Google Doc: {e}")
        return False


async def send_telegram_message(chat_id, text):
    """Send a message via the Telegram client."""
    global telegram_client
    if telegram_client and telegram_client.is_connected():
        try:
            await telegram_client.send_message(chat_id, text)
            return True
        except Exception as e:
            log("ERROR", f"Error sending Telegram message: {e}")
    return False


async def start_telegram_client():
    """Start the Telegram client using Telethon."""
    global telegram_client
    
    # Get Telegram API credentials
    credentials = await get_telegram_credentials()
    if not credentials or not credentials.get("bot_token"):
        log("ERROR", "No Telegram bot token found. Please set up credentials in the Telegram server first.")
        return None
    
    bot_token = credentials.get("bot_token")
    
    # You need api_id and api_hash from https://my.telegram.org/apps
    # For bots, we'll use a default session name
    session_name = 'mcp_client_bot'
    
    # For bots, you can use api_id=6 and api_hash='eb06d4abfb49dc3eeb1aeb98ae0f581e'
    # These are Telethon's test credentials for bots
    api_id = 6
    api_hash = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
    
    try:
        # Create the client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Connect to Telegram
        await client.start(bot_token=bot_token)
        
        # Check if the client is connected
        if await client.is_user_authorized():
            me = await client.get_me()
            log("INFO", f"Connected to Telegram as {me.username or me.first_name} (ID: {me.id})")
            
            # Set up event handlers
            @client.on(events.NewMessage(pattern='/start'))
            async def start_command(event):
                """Handle the /start command."""
                sender = await event.get_sender()
                log("TELEGRAM", f"Received /start command from {sender.id}")
                await event.respond("Hello! I'm your bot. You can send me messages and I'll process them.")
            
            @client.on(events.NewMessage(pattern='/help'))
            async def help_command(event):
                """Handle the /help command."""
                sender = await event.get_sender()
                log("TELEGRAM", f"Received /help command from {sender.id}")
                help_text = (
                    "Here are the commands you can use:\n"
                    "/start - Start the bot\n"
                    "/help - Show this help message\n\n"
                    "Special commands:\n"
                    "email:recipient@example.com|Subject|Body - Send an email\n"
                    "upload:Document Name|Document content - Create a Google Doc"
                )
                await event.respond(help_text)
            
            @client.on(events.NewMessage)
            async def message_handler(event):
                """Handle normal messages."""
                # Skip commands (they are handled by other handlers)
                if event.message.text.startswith('/'):
                    return
                
                sender = await event.get_sender()
                chat_id = event.chat_id
                text = event.message.text
                
                sender_info = f"@{sender.username}" if sender.username else f"{sender.first_name} {sender.last_name or ''}"
                log("TELEGRAM", f"Received message from {sender_info}: {text}")
                
                # Echo the message back
                # await event.respond(f"You said: {text}")
                
                # Handle special commands
                if text.startswith("email:"):
                    parts = text[6:].strip().split('|', 2)
                    if len(parts) >= 3:
                        to_email, subject, body = parts
                        if await send_gmail(to_email, subject, body):
                            await event.respond(f"Email sent to {to_email}")
                        else:
                            await event.respond("Failed to send email. Please check server logs.")
                
                elif text.startswith("upload:"):
                    parts = text[7:].strip().split('|', 1)
                    if len(parts) >= 2:
                        file_name, file_content = parts
                        if await create_google_doc(file_name, file_content):
                            await event.respond(f"Document '{file_name}' created")
                        else:
                            await event.respond("Failed to create document. Please check server logs.")
            
            # Return the connected client
            telegram_client = client
            return client
        else:
            log("ERROR", "Failed to authorize with Telegram. Check your bot token.")
            return None
    
    except Exception as e:
        log("ERROR", f"Error setting up Telegram client: {e}")
        return None


async def main():
    """Main function to start the client."""
    global telegram_client
    
    log("STARTUP", "Starting MCP Client...")
    
    # Check if Telegram server is running
    telegram_running = await check_telegram_server()
    if not telegram_running:
        log("WARNING", "Telegram server not detected. Please start it manually with:")
        log("INFO", "uvicorn mcp_server_4:app --reload --port 8000")
        return
    else:
        log("STARTUP", "Telegram server detected")
    
    # Start Google Services server
    google_started = await start_google_server()
    if not google_started:
        log("WARNING", "Could not start Google Services server. Some functionality may be limited.")
    
    # Start Telegram client
    telegram_client = await start_telegram_client()
    if not telegram_client:
        log("ERROR", "Failed to start Telegram client.")
        return
    
    log("INFO", "Client is running. Press Ctrl+C to stop.")
    
    # Keep the client running
    try:
        await telegram_client.run_until_disconnected()
    except KeyboardInterrupt:
        pass


def cleanup():
    """Clean up resources before exiting."""
    global telegram_client, google_process
    
    # Stop the Telegram client
    if telegram_client:
        log("SHUTDOWN", "Disconnecting Telegram client...")
        asyncio.run_coroutine_threadsafe(telegram_client.disconnect(), asyncio.get_event_loop())
    
    # Stop the Google Services server
    if google_process:
        log("SHUTDOWN", "Stopping Google Services server...")
        google_process.terminate()


def handle_exit(*args):
    """Handle exit signals."""
    log("SHUTDOWN", "Shutting down...")
    cleanup()
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Run the main async loop
    log("INFO", "Starting client...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_exit()