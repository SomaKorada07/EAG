"""MCP SSE Server Example with FastAPI focused on Telegram functionality"""
from mcp.server.fastmcp import Context
from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup
from typing import List, Any, Dict, Optional, Union
from dataclasses import dataclass
import urllib.parse
import sys
import traceback
import asyncio
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
import base64
from pydantic import BaseModel
import aiohttp
import telegram


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until we can make another request
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)

class DuckDuckGoSearcher:
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """Format results in a natural language style that's easier for LLMs to process"""
        if not results:
            return "No results were found for your search query. This could be due to DuckDuckGo's bot detection or the query returned no matches. Please try rephrasing your search or try again in a few minutes."

        output = []
        output.append(f"Found {len(results)} search results:\n")

        for result in results:
            output.append(f"{result.position}. {result.title}")
            output.append(f"   URL: {result.link}")
            output.append(f"   Summary: {result.snippet}")
            output.append("")  # Empty line between results

        return "\n".join(output)

    async def search(
        self, query: str, ctx: Context, max_results: int = 10
    ) -> List[SearchResult]:
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Create form data for POST request
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            await ctx.info(f"Searching DuckDuckGo for: {query}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            if not soup:
                await ctx.error("Failed to parse HTML response")
                return []

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")

                # Skip ad results
                if "y.js" in link:
                    continue

                # Clean up DuckDuckGo redirect URLs
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append(
                    SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        position=len(results) + 1,
                    )
                )

                if len(results) >= max_results:
                    break

            await ctx.info(f"Successfully found {len(results)} results")
            return results

        except httpx.TimeoutException:
            await ctx.error("Search request timed out")
            return []
        except httpx.HTTPError as e:
            await ctx.error(f"HTTP error occurred: {str(e)}")
            return []
        except Exception as e:
            await ctx.error(f"Unexpected error during search: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return []


class CredentialManager:
    """Securely manage API credentials for different services."""
    
    def __init__(self, credentials_file: str = "credentials.json"):
        self.credentials_path = Path(credentials_file)
        self._credentials = self._load_credentials()
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from file or create empty structure if file doesn't exist."""
        if self.credentials_path.exists():
            try:
                with open(self.credentials_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"telegram": {}}
        else:
            return {"telegram": {}}
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        with open(self.credentials_path, "w") as f:
            json.dump(self._credentials, f)
    
    def get_credentials(self, service: str) -> Dict[str, Any]:
        """Get credentials for a specific service."""
        return self._credentials.get(service, {})
    
    def set_credentials(self, service: str, credentials: Dict[str, Any]) -> None:
        """Set credentials for a specific service."""
        self._credentials[service] = credentials
        self._save_credentials()
    
    def update_credentials(self, service: str, key: str, value: str) -> None:
        """Update a specific credential for a service."""
        if service not in self._credentials:
            self._credentials[service] = {}
        self._credentials[service][key] = value
        self._save_credentials()


# Input models for Telegram operations
class TelegramMessageInput(BaseModel):
    message: str
    chat_id: Optional[str] = None
    parse_mode: Optional[str] = None
    disable_notification: Optional[bool] = False
    reply_to_message_id: Optional[int] = None

class TelegramPhotoInput(BaseModel):
    photo_path: str
    caption: Optional[str] = None
    chat_id: Optional[str] = None
    disable_notification: Optional[bool] = False

class TelegramDocumentInput(BaseModel):
    document_path: str
    caption: Optional[str] = None
    chat_id: Optional[str] = None
    disable_notification: Optional[bool] = False

class CredentialInput(BaseModel):
    service: str
    key: str
    value: str

# Models for Telegram webhook
class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

class TelegramChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class TelegramMessageEntity(BaseModel):
    type: str
    offset: int
    length: int
    url: Optional[str] = None
    user: Optional[TelegramUser] = None
    language: Optional[str] = None

class TelegramMessage(BaseModel):
    message_id: int
    from_user: Optional[TelegramUser] = None
    date: int
    chat: TelegramChat
    text: Optional[str] = None
    entities: Optional[List[TelegramMessageEntity]] = None
    photo: Optional[List[Dict[str, Any]]] = None
    document: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None
    
    class Config:
        fields = {
            'from_user': 'from'
        }

class TelegramWebhookUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None
    edited_channel_post: Optional[TelegramMessage] = None

# Initialize credential manager
credential_manager = CredentialManager()

mcp: FastMCP = FastMCP("Telegram")


@mcp.tool()
async def send_telegram_message(input: TelegramMessageInput, ctx: Context) -> str:
    """
    Send a message via Telegram using the official Python Telegram Bot API.
    
    Args:
        input: The message details including message content and optional chat ID
        ctx: MCP context for logging
    
    Returns:
        str: Confirmation of message sent or error details
    """
    try:
        credentials = credential_manager.get_credentials("telegram")
        
        if not credentials.get("bot_token"):
            await ctx.error("Telegram bot token not found. Please set credentials first.")
            return "Error: Telegram credentials not configured. Use set_telegram_credentials tool first."
        
        bot_token = credentials["bot_token"]
        chat_id = input.chat_id or credentials.get("default_chat_id")
        
        if not chat_id:
            await ctx.error("No chat ID provided or default chat ID configured.")
            return "Error: No chat ID provided. Please specify a chat ID or set a default one."
        
        await ctx.info(f"Initializing Telegram bot with token {bot_token[:5]}...")
        
        # Using python-telegram-bot library (asynchronous)
        async with aiohttp.ClientSession() as session:
            bot = telegram.Bot(token=bot_token, session=session)
            
            # Check if the bot is valid by getting its information
            bot_info = await bot.get_me()
            await ctx.info(f"Connected as bot: {bot_info.username}")
            
            # Use provided parse mode or auto-detect
            parse_mode = input.parse_mode
            message_text = input.message
            
            if not parse_mode:
                # Determine if we should use Markdown or HTML parsing
                has_markdown = any(marker in input.message for marker in ['*', '_', '`', '```', '[', ']('])
                has_html = any(marker in input.message for marker in ['<b>', '<i>', '<code>', '<pre>'])
                
                if has_markdown and not has_html:
                    parse_mode = telegram.constants.ParseMode.MARKDOWN_V2
                    # Escape special characters for MARKDOWN_V2
                    message_text = input.message.replace('.', '\\.').replace('-', '\\-').replace('!', '\\!')
                elif has_html and not has_markdown:
                    parse_mode = telegram.constants.ParseMode.HTML
            
            # Send message with appropriate parse mode
            message = await bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode=parse_mode,
                disable_notification=input.disable_notification,
                reply_to_message_id=input.reply_to_message_id
            )
            
            await ctx.info(f"Message sent to Telegram chat {chat_id}, message ID: {message.message_id}")
            return f"Message sent successfully to Telegram chat {chat_id}, message ID: {message.message_id}"
    
    except telegram.error.Unauthorized:
        error_msg = "Unauthorized: Invalid bot token"
        await ctx.error(error_msg)
        return error_msg
    except telegram.error.BadRequest as e:
        error_msg = f"Bad request: {str(e)}"
        await ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send Telegram message: {str(e)}"
        await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def send_telegram_photo(input: TelegramPhotoInput, ctx: Context) -> str:
    """
    Send a photo via Telegram using the official Python Telegram Bot API.
    
    Args:
        input: The photo details including photo path, optional caption, and chat ID
        ctx: MCP context for logging
    
    Returns:
        str: Confirmation of photo sent or error details
    """
    try:
        credentials = credential_manager.get_credentials("telegram")
        
        if not credentials.get("bot_token"):
            await ctx.error("Telegram bot token not found. Please set credentials first.")
            return "Error: Telegram credentials not configured. Use set_telegram_credentials tool first."
        
        bot_token = credentials["bot_token"]
        chat_id = input.chat_id or credentials.get("default_chat_id")
        
        if not chat_id:
            await ctx.error("No chat ID provided or default chat ID configured.")
            return "Error: No chat ID provided. Please specify a chat ID or set a default one."
        
        # Check if photo file exists
        if not os.path.exists(input.photo_path):
            await ctx.error(f"Photo file not found: {input.photo_path}")
            return f"Error: Photo file not found: {input.photo_path}"
        
        await ctx.info(f"Initializing Telegram bot with token {bot_token[:5]}...")
        
        # Using python-telegram-bot library (asynchronous)
        async with aiohttp.ClientSession() as session:
            bot = telegram.Bot(token=bot_token, session=session)
            
            # Check if the bot is valid by getting its information
            bot_info = await bot.get_me()
            await ctx.info(f"Connected as bot: {bot_info.username}")
            
            # Send photo
            await ctx.info(f"Sending photo: {input.photo_path}")
            with open(input.photo_path, "rb") as photo_file:
                message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=input.caption,
                    disable_notification=input.disable_notification
                )
            
            await ctx.info(f"Photo sent to Telegram chat {chat_id}, message ID: {message.message_id}")
            return f"Photo sent successfully to Telegram chat {chat_id}, message ID: {message.message_id}"
    
    except telegram.error.Unauthorized:
        error_msg = "Unauthorized: Invalid bot token"
        await ctx.error(error_msg)
        return error_msg
    except telegram.error.BadRequest as e:
        error_msg = f"Bad request: {str(e)}"
        await ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send Telegram photo: {str(e)}"
        await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def send_telegram_document(input: TelegramDocumentInput, ctx: Context) -> str:
    """
    Send a document/file via Telegram using the official Python Telegram Bot API.
    
    Args:
        input: The document details including file path, optional caption, and chat ID
        ctx: MCP context for logging
    
    Returns:
        str: Confirmation of document sent or error details
    """
    try:
        credentials = credential_manager.get_credentials("telegram")
        
        if not credentials.get("bot_token"):
            await ctx.error("Telegram bot token not found. Please set credentials first.")
            return "Error: Telegram credentials not configured. Use set_telegram_credentials tool first."
        
        bot_token = credentials["bot_token"]
        chat_id = input.chat_id or credentials.get("default_chat_id")
        
        if not chat_id:
            await ctx.error("No chat ID provided or default chat ID configured.")
            return "Error: No chat ID provided. Please specify a chat ID or set a default one."
        
        # Check if document file exists
        if not os.path.exists(input.document_path):
            await ctx.error(f"Document file not found: {input.document_path}")
            return f"Error: Document file not found: {input.document_path}"
        
        await ctx.info(f"Initializing Telegram bot with token {bot_token[:5]}...")
        
        # Using python-telegram-bot library (asynchronous)
        async with aiohttp.ClientSession() as session:
            bot = telegram.Bot(token=bot_token, session=session)
            
            # Check if the bot is valid by getting its information
            bot_info = await bot.get_me()
            await ctx.info(f"Connected as bot: {bot_info.username}")
            
            # Send document
            await ctx.info(f"Sending document: {input.document_path}")
            with open(input.document_path, "rb") as document_file:
                message = await bot.send_document(
                    chat_id=chat_id,
                    document=document_file,
                    caption=input.caption,
                    disable_notification=input.disable_notification
                )
            
            await ctx.info(f"Document sent to Telegram chat {chat_id}, message ID: {message.message_id}")
            return f"Document sent successfully to Telegram chat {chat_id}, message ID: {message.message_id}"
    
    except telegram.error.Unauthorized:
        error_msg = "Unauthorized: Invalid bot token"
        await ctx.error(error_msg)
        return error_msg
    except telegram.error.BadRequest as e:
        error_msg = f"Bad request: {str(e)}"
        await ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send Telegram document: {str(e)}"
        await ctx.error(error_msg)
        return error_msg


@mcp.tool()
async def set_telegram_credentials(input: CredentialInput, ctx: Context) -> str:
    """
    Set credentials for Telegram.
    
    Args:
        input: The credential details including key and value
        ctx: MCP context for logging
    
    Returns:
        str: Confirmation of credential update or error details
    """
    try:
        if input.service != "telegram":
            await ctx.error(f"Invalid service: {input.service}")
            return f"Error: This tool only accepts 'telegram' as the service name"
        
        credential_manager.update_credentials("telegram", input.key, input.value)
        
        # Mask the credential value for privacy in logs
        masked_value = input.value[:3] + "*" * (len(input.value) - 3) if len(input.value) > 3 else "***"
        await ctx.info(f"Telegram credentials updated: {input.key}")
        
        return f"Successfully updated Telegram credential: {input.key}"
    
    except Exception as e:
        error_msg = f"Failed to set Telegram credentials: {str(e)}"
        await ctx.error(error_msg)
        return error_msg


# Handler for incoming Telegram messages
async def handle_telegram_message(message: TelegramMessage):
    """
    Process incoming Telegram messages and respond appropriately.
    
    Args:
        message: The incoming Telegram message
    """
    if not message.text:
        # Skip messages without text
        return
    
    try:
        # Get bot token for replying
        credentials = credential_manager.get_credentials("telegram")
        if not credentials.get("bot_token"):
            print("ERROR: No bot token available for replying to message")
            return
            
        bot_token = credentials["bot_token"]
        chat_id = str(message.chat.id)
        
        # Log received message
        user_name = message.from_user.username or f"{message.from_user.first_name} {message.from_user.last_name or ''}"
        print(f"Received message from {user_name} in chat {chat_id}: {message.text}")
        
        # Process the message with your AI or logic
        # This is where you would integrate with your MCP tools
        if message.text.startswith("/"):
            # Handle commands
            command = message.text.split()[0].lower()
            if command == "/start":
                response_text = "Hello! I'm your Telegram bot. I can help you with various tasks."
            elif command == "/help":
                response_text = "Available commands:\n/start - Start the bot\n/help - Show this help message"
            else:
                response_text = f"Unknown command: {command}"
        else:
            # Process normal messages - you can use any of your MCP tools here
            # For now, we'll just echo the message
            response_text = f"You said: {message.text}"
        
        # Reply to the user
        async with aiohttp.ClientSession() as session:
            bot = telegram.Bot(token=bot_token, session=session)
            await bot.send_message(
                chat_id=chat_id,
                text=response_text
            )
            
    except Exception as e:
        print(f"ERROR handling Telegram message: {str(e)}")


# Verify Telegram webhook requests
async def verify_telegram_webhook(request: Request):
    """
    Verify that the webhook request is from Telegram.
    
    Args:
        request: The incoming request
        
    Returns:
        bool: True if verified, False otherwise
    """
    credentials = credential_manager.get_credentials("telegram")
    
    # If no secret token is set, accept all requests (not recommended for production)
    if not credentials.get("webhook_secret"):
        return True
        
    # Check the X-Telegram-Bot-Api-Secret-Token header
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not secret_header or secret_header != credentials.get("webhook_secret"):
        return False
        
    return True


# Create FastAPI app and mount the SSE MCP server
app = FastAPI(title="Telegram MCP Server")


@app.get("/test")
async def test():
    """
    Test endpoint to verify the server is running.

    Returns:
        dict: A simple hello world message.
    """
    return {"message": "Hello, world!"}


@app.get("/get_telegram_credentials")
async def get_telegram_credentials():
    """
    Get the Telegram credentials for the client.
    Only returns the bot token and default chat ID, not any sensitive API keys.
    
    Returns:
        dict: The Telegram credentials
    """
    creds = credential_manager.get_credentials("telegram")
    return {
        "bot_token": creds.get("bot_token", ""),
        "default_chat_id": creds.get("default_chat_id", "")
    }


@app.post("/webhook/telegram")
async def telegram_webhook(update: TelegramWebhookUpdate, request: Request):
    """
    Webhook endpoint for receiving updates from Telegram.
    
    Args:
        update: The update object from Telegram
        request: The request object
        
    Returns:
        dict: A simple OK response
    """
    # Verify the webhook request
    if not await verify_telegram_webhook(request):
        raise HTTPException(status_code=403, detail="Unauthorized webhook request")
    
    # Process the message asynchronously
    if update.message:
        asyncio.create_task(handle_telegram_message(update.message))
    elif update.edited_message:
        # You can handle edited messages differently if needed
        asyncio.create_task(handle_telegram_message(update.edited_message))
    
    # Always return 200 OK to Telegram quickly
    return {"status": "ok"}


@app.post("/set_webhook")
async def set_webhook(webhook_url: str, secret_token: Optional[str] = None):
    """
    Set up a Telegram webhook.
    
    Args:
        webhook_url: The full URL to your webhook endpoint
        secret_token: Optional secret token for additional security
        
    Returns:
        dict: Result of the webhook setup
    """
    try:
        credentials = credential_manager.get_credentials("telegram")
        
        if not credentials.get("bot_token"):
            return {"success": False, "error": "No bot token configured. Set bot_token first."}
            
        bot_token = credentials["bot_token"]
        
        # Build the webhook URL
        if not webhook_url.endswith("/webhook/telegram"):
            if webhook_url.endswith("/"):
                webhook_url += "webhook/telegram"
            else:
                webhook_url += "/webhook/telegram"
                
        # Set up the webhook
        async with aiohttp.ClientSession() as session:
            # First, get bot info to verify token
            telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with session.get(telegram_api_url) as response:
                if response.status != 200:
                    return {"success": False, "error": "Invalid bot token"}
            
            # Configure the webhook
            params = {"url": webhook_url}
            if secret_token:
                params["secret_token"] = secret_token
                # Save the secret token to verify incoming requests
                credential_manager.update_credentials("telegram", "webhook_secret", secret_token)
                
            # Set the webhook
            set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            async with session.post(set_webhook_url, json=params) as response:
                result = await response.json()
                if response.status == 200 and result.get("ok"):
                    return {"success": True, "webhook_url": webhook_url, "details": result}
                else:
                    return {"success": False, "error": "Failed to set webhook", "details": result}
                    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/remove_webhook")
async def remove_webhook():
    """
    Remove the Telegram webhook.
    
    Returns:
        dict: Result of the webhook removal
    """
    try:
        credentials = credential_manager.get_credentials("telegram")
        
        if not credentials.get("bot_token"):
            return {"success": False, "error": "No bot token configured. Set bot_token first."}
            
        bot_token = credentials["bot_token"]
        
        # Remove the webhook
        async with aiohttp.ClientSession() as session:
            remove_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            async with session.post(remove_webhook_url) as response:
                result = await response.json()
                if response.status == 200 and result.get("ok"):
                    # Clear the webhook secret if it exists
                    if credentials.get("webhook_secret"):
                        credential_manager.update_credentials("telegram", "webhook_secret", "")
                    return {"success": True, "details": result}
                else:
                    return {"success": False, "error": "Failed to remove webhook", "details": result}
                    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/set_credentials")
async def set_credentials_endpoint(service: str, key: str, value: str):
    """
    Endpoint to set credentials directly.
    
    Args:
        service: The service name (e.g., "telegram")
        key: The credential key (e.g., "bot_token")
        value: The value to set
    
    Returns:
        dict: Result of the operation
    """
    try:
        if service != "telegram":
            return {"success": False, "error": "This endpoint only accepts 'telegram' as the service name"}
        
        credential_manager.update_credentials(service, key, value)
        
        # Mask the credential value for privacy in logs
        masked_value = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
        print(f"Credentials updated for {service}: {key} = {masked_value}")
        
        return {"success": True, "message": f"Successfully updated {service} credential: {key}"}
    
    except Exception as e:
        error_msg = f"Failed to set credentials: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {"success": False, "error": error_msg}


# Mount the SSE MCP server after defining our routes
app.mount("/", mcp.sse_app())