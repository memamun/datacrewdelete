from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict
from pydantic import BaseModel, Field
from simplegmail import Gmail
import base64
from bs4 import BeautifulSoup
import os
from datetime import datetime
from dotenv import load_dotenv
import logging


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_reader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class EmailReaderInput(BaseModel):
    """Input schema for EmailReaderTool."""
    max_results: int = Field(default=10, description="Maximum number of emails to retrieve")
    mark_as_read: bool = Field(default=True, description="Whether to mark emails as read")

class EmailReaderTool(BaseTool):
    name: str = "Email Reader"
    description: str = "Reads the last 10 unread emails from Gmail inbox"
    args_schema: Type[BaseModel] = EmailReaderInput

    def __init__(self):
        super().__init__()
        logger.debug("Initializing EmailReaderTool")
        try:
            self._initialize_gmail()
        except Exception as e:
            logger.error(f"Gmail initialization failed: {e}", exc_info=True)
            self._gmail = None

    def _initialize_gmail(self):
        """Initialize Gmail client."""
        logger.debug("Starting Gmail initialization")
        
        # Try multiple possible locations for the client secret file
        client_secret_file = os.getenv('GMAIL_CLIENT_SECRET_FILE') or 'client_secret.json'
        possible_locations = [
            client_secret_file,
            os.path.join('credentials', 'client_secret.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'client_secret.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'credentials', 'client_secret.json')
        ]
        
        logger.debug(f"Checking possible locations: {possible_locations}")
        
        # Find the first existing file
        for location in possible_locations:
            logger.debug(f"Checking location: {location}")
            if os.path.exists(location):
                client_secret_file = location
                logger.debug(f"Found client secret file at: {client_secret_file}")
                break
        else:
            error_msg = f"Client secret file not found in any of these locations: {possible_locations}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            self._gmail = Gmail(client_secret_file=client_secret_file)
            logger.debug("Gmail initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail with file {client_secret_file}: {e}")
            raise

    def _get_message_body(self, payload) -> str:
        """Extract and clean message body from email payload."""
        logger.debug("Extracting message body")
        body = ''
        try:
            if 'parts' in payload:
                logger.debug("Processing multipart message")
                # First try to find text/plain part
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            return self._clean_text(body)
                
                # If no text/plain, try html
                for part in payload['parts']:
                    if part['mimeType'] == 'text/html':
                        data = part['body'].get('data', '')
                        if data:
                            html = base64.urlsafe_b64decode(data).decode('utf-8')
                            return self._clean_html(html)
            else:
                logger.debug("Processing single part message")
                data = payload['body'].get('data', '')
                if data:
                    content = base64.urlsafe_b64decode(data).decode('utf-8')
                    if payload.get('mimeType') == 'text/html':
                        return self._clean_html(content)
                    return self._clean_text(content)
            
            return body.strip()
        except Exception as e:
            logger.error(f"Error processing message body: {e}", exc_info=True)
            return f"Error processing message body: {str(e)}"

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract readable text."""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "head"]):
                script.decompose()
            
            # Remove all links but keep their text
            for a in soup.find_all('a'):
                a.replace_with(a.get_text())
            
            # Get text and clean it
            text = soup.get_text(separator='\n')
            return self._clean_text(text)
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return self._clean_text(html_content)

    def _clean_text(self, text: str) -> str:
        """Clean and format plain text content."""
        try:
            # Split into lines and remove empty ones
            lines = [line.strip() for line in text.splitlines()]
            lines = [line for line in lines if line]
            
            # Remove common noise
            cleaned_lines = []
            for line in lines:
                # Skip lines that look like URLs, CSS, or other noise
                if any(skip in line.lower() for skip in [
                    'http://', 'https://', 
                    '{', '}', '</', 
                    'font-family:', 'color:', 
                    'xmlns:', 'javascript:',
                    '͏ ͏ ͏'
                ]):
                    continue
                cleaned_lines.append(line)
            
            # Join lines and clean up extra whitespace
            text = '\n'.join(cleaned_lines)
            text = ' '.join(text.split())
            
            # Truncate if too long (e.g., first 1000 characters)
            if len(text) > 1000:
                text = text[:997] + "..."
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text.strip()

    def _format_email_info(self, message) -> Dict:
        """Format email information into a dictionary."""
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown Date')
        
        return {
            "message_id": message['id'],
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": self._get_message_body(message['payload'])
        }

    def _run(self, max_results: int = 10, mark_as_read: bool = True) -> str:
        """Read unread emails from Gmail inbox."""
        logger.debug(f"Reading last {max_results} unread emails")
        
        if not self._gmail:
            return "Email service not initialized properly"
            
        try:
            # Search for unread messages in inbox
            response = self._gmail.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=max_results
            ).execute()

            messages = response.get('messages', [])
            if not messages:
                return "No unread emails found"

            email_data = []
            for msg in messages:
                message = self._gmail.service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                email_info = self._format_email_info(message)
                email_data.append(email_info)
                
                if mark_as_read:
                    self._gmail.service.users().messages().modify(
                        userId='me',
                        id=msg['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    logger.debug(f"Marked message {msg['id']} as read")

            # Format output
            output = "Last {len(email_data)} unread emails:\n\n"
            for idx, email in enumerate(email_data, 1):
                output += f"Email {idx}:\n"
                output += f"From: {email['sender']}\n"
                output += f"Subject: {email['subject']}\n"
                output += f"Date: {email['date']}\n"
                output += f"Body:\n{email['body'][:500]}...\n\n"  # First 500 chars of body
                output += "-" * 80 + "\n\n"

            return output

        except Exception as e:
            logger.error(f"Error reading emails: {e}", exc_info=True)
            return f"Error reading emails: {str(e)}"