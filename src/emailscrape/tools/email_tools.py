from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from simplegmail import Gmail
import base64
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_tools.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class EmailSenderInput(BaseModel):
    """Input schema for EmailSenderTool."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    html_content: Optional[str] = Field(None, description="Optional HTML content")

class EmailCheckerInput(BaseModel):
    """Input schema for EmailCheckerTool."""
    subject: str = Field(..., description="Subject to search for")
    from_email: str = Field(..., description="Sender email to filter")

class EmailSenderTool(BaseTool):
    name: str = "Email Sender"
    description: str = "Sends emails using Gmail API"
    args_schema: Type[BaseModel] = EmailSenderInput

    def __init__(self):
        super().__init__()
        logger.debug("Initializing EmailSenderTool")
        try:
            self._initialize_gmail()
        except Exception as e:
            logger.error(f"Gmail initialization failed: {e}", exc_info=True)
            self._gmail = None
            self._sender_email = None

    def _initialize_gmail(self):
        logger.debug("Starting Gmail initialization")
        client_secret_file = os.getenv('GMAIL_CLIENT_SECRET_FILE', 'client_secret.json')
        logger.debug(f"Using client secret file: {client_secret_file}")
        
        if not os.path.exists(client_secret_file):
            logger.error(f"Client secret file not found: {client_secret_file}")
            raise FileNotFoundError(f"Client secret file not found: {client_secret_file}")
        
        self._gmail = Gmail(client_secret_file=client_secret_file)
        self._sender_email = os.getenv('SENDER_EMAIL')
        
        if not self._sender_email:
            logger.error("SENDER_EMAIL environment variable not set")
            raise ValueError("SENDER_EMAIL environment variable not set")
        
        logger.debug(f"Gmail initialized successfully with sender email: {self._sender_email}")

    def _run(self, to: str, subject: str, body: str, html_content: Optional[str] = None) -> str:
        logger.debug(f"Attempting to send email to: {to}")
        logger.debug(f"Input types - to: {type(to)}, subject: {type(subject)}, body: {type(body)}")
        
        if not self._gmail:
            logger.error("Email service not initialized properly")
            return "Email service not initialized properly"
        
        try:
            # Handle potential JSON string input
            if isinstance(to, str) and to.startswith('{'):
                try:
                    data = json.loads(to)
                    to = data.get('to', to)
                    subject = data.get('subject', subject)
                    body = data.get('body', body)
                    html_content = data.get('html_content', html_content)
                    logger.debug("Successfully parsed JSON input")
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON input, using raw string")
            
            # Ensure all inputs are strings
            to = str(to)
            subject = str(subject)
            body = str(body)
            
            logger.debug(f"Preparing email parameters for: {to}")
            logger.debug(f"Email body preview: {body[:100]}...")
            
            params = {
                "to": to,
                "sender": self._sender_email,
                "subject": subject,
                "msg_plain": body,
                "signature": True
            }
            
            if html_content:
                logger.debug("Adding HTML content to email")
                params["msg_html"] = str(html_content)

            logger.debug("Sending email with params: %s", {k: v[:100] if isinstance(v, str) else v for k, v in params.items()})
            message = self._gmail.send_message(**params)
            logger.info(f"Email sent successfully to {to}")
            
            return (
                f"Email sent successfully to {to}!\n"
                f"Subject: {subject}\n"
                f"Body preview: {body[:100]}..."
            )
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return f"Failed to send email: {str(e)}"

class EmailCheckerTool(BaseTool):
    name: str = "Email Response Checker"
    description: str = "Checks for unread email responses with specific subject and sender"
    args_schema: Type[BaseModel] = EmailCheckerInput

    def __init__(self):
        super().__init__()
        logger.debug("Initializing EmailCheckerTool")
        try:
            self._initialize_gmail()
        except Exception as e:
            logger.error(f"Gmail initialization failed: {e}", exc_info=True)
            self._gmail = None

    def _initialize_gmail(self):
        logger.debug("Starting Gmail initialization for checker")
        client_secret_file = os.getenv('GMAIL_CLIENT_SECRET_FILE', 'client_secret.json')
        logger.debug(f"Using client secret file: {client_secret_file}")
        
        if not os.path.exists(client_secret_file):
            logger.error(f"Client secret file not found: {client_secret_file}")
            raise FileNotFoundError(f"Client secret file not found: {client_secret_file}")
            
        self._gmail = Gmail(client_secret_file=client_secret_file)
        logger.debug("Gmail checker initialized successfully")

    def _run(self, subject: str, from_email: str) -> str:
        logger.debug(f"Checking emails from: {from_email} with subject: {subject}")
        
        if not self._gmail:
            logger.error("Email service not initialized properly")
            return "Email service not initialized properly"
            
        try:
            # Convert potential dictionary inputs to strings
            subject = str(subject)
            from_email = str(from_email)
            
            logger.debug("Calling _check_emails method")
            email_data = self._check_emails(subject, from_email)
            
            if email_data:
                logger.info(f"Found {len(email_data)} matching emails")
                return str(email_data)
            
            logger.info("No matching emails found")
            return "No matching emails found"
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}", exc_info=True)
            return f"Error checking emails: {str(e)}"

    def _check_emails(self, subject: str, from_email: str):
        logger.debug(f"Searching for emails - Subject: {subject}, From: {from_email}")
        try:
            query = f'from:{from_email} subject:{subject} is:unread'
            logger.debug(f"Gmail API query: {query}")
            
            response = self._gmail.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q=query
            ).execute()

            messages = response.get('messages', [])
            logger.debug(f"Found {len(messages) if messages else 0} messages")
            
            if not messages:
                return []

            email_data = []
            for msg in messages:
                logger.debug(f"Processing message ID: {msg['id']}")
                message = self._gmail.service.users().messages().get(
                    userId='me', id=msg['id']
                ).execute()

                headers = message['payload']['headers']
                email_info = {
                    "subject": next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject'),
                    "sender": next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender'),
                    "body": self._get_message_body(message['payload'])
                }
                email_data.append(email_info)
                logger.debug(f"Processed email from: {email_info['sender']}")

                # Mark as read
                logger.debug(f"Marking message {msg['id']} as read")
                self._gmail.service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

            return email_data
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}", exc_info=True)
            return f"Error processing emails: {str(e)}"

    def _get_message_body(self, payload):
        logger.debug("Extracting message body")
        body = ''
        try:
            if 'parts' in payload:
                logger.debug("Processing multipart message")
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        logger.debug("Found text/plain part")
                        body += base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                    elif part['mimeType'] == 'text/html':
                        logger.debug("Found text/html part")
                        html = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')
                        body += soup.get_text()
            else:
                logger.debug("Processing single part message")
                data = payload['body'].get('data', '')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
            return body
        except Exception as e:
            logger.error(f"Error processing message body: {e}", exc_info=True)
            return f"Error processing message body: {str(e)}"