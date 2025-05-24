from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import os
import json
import faiss
import numpy as np
from pathlib import Path
import requests
from markitdown import MarkItDown
import time
from models import AddInput, AddOutput, SqrtInput, SqrtOutput, StringsToIntsInput, StringsToIntsOutput, ExpSumInput, ExpSumOutput, ShellCommandInput
from PIL import Image as PILImage
from tqdm import tqdm
import hashlib
from pydantic import BaseModel
import subprocess
import sqlite3
import base64
from typing import Dict, List, Optional, Any, Union
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import aiofiles
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from io import BytesIO
import pickle


class PythonCodeInput(BaseModel):
    code: str


class PythonCodeOutput(BaseModel):
    result: str


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
                return {"gmail": {}, "gdrive": {}}
        else:
            return {"gmail": {}, "gdrive": {}}
    
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


# Input models for Google service operations
class GmailMessageInput(BaseModel):
    to: str
    subject: str
    body: str
    attachments: Optional[List[str]] = None

class GDriveFileInput(BaseModel):
    name: str
    content: Optional[str] = None
    parent_folder_id: Optional[str] = None
    file_path: Optional[str] = None

class CredentialInput(BaseModel):
    service: str
    key: str
    value: str

# Initialize credential manager
credential_manager = CredentialManager()

mcp = FastMCP("Google")


@mcp.tool()
def send_gmail_message(input: GmailMessageInput) -> str:
    """
    Send an email via Gmail with advanced options using SMTP.
    
    Args:
        input: Email details including recipient, subject, body, and optional attachments
    
    Returns:
        str: Confirmation of email sent or error details
    """
    try:
        credentials = credential_manager.get_credentials("gmail")
        
        if not credentials.get("email") or not credentials.get("app_password"):
            print("ERROR: Gmail credentials not found. Please set credentials first.")
            return "Error: Gmail credentials not configured. Use set_service_credentials tool first."
        
        email_from = credentials["email"]
        app_password = credentials["app_password"]
        
        print(f"Preparing email from {email_from} to {input.to}")
        
        # Create a multipart message
        message = MIMEMultipart()
        message["From"] = email_from
        message["To"] = input.to
        message["Subject"] = input.subject
        
        # Add message body
        message.attach(MIMEText(input.body, "html"))
        
        # Add attachments if any
        attachments_info = ""
        if input.attachments and len(input.attachments) > 0:
            attachments_info = f" with {len(input.attachments)} attachments"
            
            for attachment_path in input.attachments:
                try:
                    with open(attachment_path, "rb") as file:
                        attachment = MIMEApplication(file.read())
                        attachment_name = os.path.basename(attachment_path)
                        attachment.add_header(
                            "Content-Disposition", 
                            f"attachment; filename={attachment_name}"
                        )
                        message.attach(attachment)
                except Exception as attach_err:
                    print(f"ERROR: Failed to attach file {attachment_path}: {str(attach_err)}")
        
        # Connect to Gmail SMTP server and send the email
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        print("Connected to SMTP server")
        
        server.login(email_from, app_password)
        print("Authenticated with Gmail")
        
        server.send_message(message)
        server.quit()
        
        print(f"Email sent to {input.to}{attachments_info}")
        return f"Email sent successfully from {email_from} to {input.to}{attachments_info}"
    
    except Exception as e:
        error_msg = f"Failed to send Gmail: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg




@mcp.tool()
def manage_gdrive_file(input: GDriveFileInput) -> str:
    """
    Create, upload, or access files on Google Drive using the official Google API.
    
    Args:
        input: File details including name, optional content, parent folder, or file path
    
    Returns:
        str: Confirmation of operation or error details
    """
    try:
        # Constants for Google API
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        TOKEN_PATH = 'token.pickle'
        CREDENTIALS_PATH = 'credentials.json'
        
        credentials = credential_manager.get_credentials("gdrive")
        
        if not credentials.get("client_id") or not credentials.get("client_secret"):
            print("ERROR: Google Drive credentials not found. Please set client_id and client_secret first.")
            return "Error: Google Drive credentials not configured. Use set_service_credentials tool first."
        
        # Try to load saved token
        creds = None
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials available, let user login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing Google Drive credentials")
                creds.refresh(Request())
            else:
                # Save credentials for the user
                client_config = {
                    "installed": {
                        "client_id": credentials.get("client_id"),
                        "client_secret": credentials.get("client_secret"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
                
                # Create temporary credentials file
                with open(CREDENTIALS_PATH, 'w') as creds_file:
                    json.dump(client_config, creds_file)
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
                
                # Remove temporary credentials file
                if os.path.exists(CREDENTIALS_PATH):
                    os.remove(CREDENTIALS_PATH)
        
        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)
        print("Connected to Google Drive API")
        
        print(f"Google Drive operation: creating file '{input.name}'")
        
        file_metadata = {
            'name': input.name,
        }
        
        # Set parent folder if provided
        if input.parent_folder_id:
            file_metadata['parents'] = [input.parent_folder_id]
            
        # Choose upload method based on input
        if input.content:
            # Create file from content string
            media = MediaIoBaseUpload(
                BytesIO(input.content.encode('utf-8')),
                mimetype='text/plain'
            )
            file_type = "document with content"
            
        elif input.file_path:
            # Upload file from path
            if not os.path.exists(input.file_path):
                print(f"ERROR: File not found: {input.file_path}")
                return f"Error: File not found: {input.file_path}"
                
            # Guess mimetype based on file extension
            mimetype = 'application/octet-stream'  # Default
            if input.file_path.lower().endswith('.pdf'):
                mimetype = 'application/pdf'
            elif input.file_path.lower().endswith(('.jpg', '.jpeg')):
                mimetype = 'image/jpeg'
            elif input.file_path.lower().endswith('.png'):
                mimetype = 'image/png'
            elif input.file_path.lower().endswith('.txt'):
                mimetype = 'text/plain'
            elif input.file_path.lower().endswith(('.doc', '.docx')):
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            media = MediaFileUpload(input.file_path, mimetype=mimetype)
            file_type = f"file from path {input.file_path}"
            
        else:
            # Create empty file (Google Doc)
            media = None
            file_type = "empty file"
        
        # Upload file to Drive
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        # Get the file's web view link
        file_id = file.get('id')
        file_link = file.get('webViewLink', f'https://drive.google.com/file/d/{file_id}')
        folder_info = f" in folder {input.parent_folder_id}" if input.parent_folder_id else ""
        
        print(f"File '{input.name}' created on Google Drive with ID: {file_id}")
        return f"Successfully created {file_type} '{input.name}'{folder_info} on Google Drive\nFile ID: {file_id}\nLink: {file_link}"
    
    except Exception as e:
        error_msg = f"Failed to perform Google Drive operation: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg


@mcp.tool()
def set_google_credentials(input: CredentialInput) -> str:
    """
    Set credentials for Google services (Gmail and Google Drive).
    
    Args:
        input: The credential details including service name, key, and value
    
    Returns:
        str: Confirmation of credential update or error details
    """
    try:
        if input.service not in ["gmail", "gdrive"]:
            print(f"ERROR: Invalid service: {input.service}")
            return f"Error: Invalid service '{input.service}'. Must be one of: gmail, gdrive"
        
        credential_manager.update_credentials(input.service, input.key, input.value)
        
        # Mask the credential value for privacy in logs
        masked_value = input.value[:3] + "*" * (len(input.value) - 3) if len(input.value) > 3 else "***"
        print(f"Credentials updated for {input.service}: {input.key} = {masked_value}")
        
        return f"Successfully updated {input.service} credential: {input.key}"
    
    except Exception as e:
        error_msg = f"Failed to set Google credentials: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg
