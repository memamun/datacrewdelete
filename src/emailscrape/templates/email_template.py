from typing import TypedDict, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

@dataclass
class EmailContext:
    user_name: str
    user_email: str
    website_name: str
    user_location: Optional[str] = None
    privacy_law: str = "GDPR and CCPA"
    response_timeframe: int = 30
    timestamp: str = datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def from_env(cls, website_name: str):
        load_dotenv()
        return cls(
            user_name=os.getenv('USER_NAME', ''),
            user_email=os.getenv('USER_EMAIL', ''),
            website_name=website_name,
            user_location=os.getenv('USER_LOCATION', ''),
            privacy_law=os.getenv('PRIVACY_LAWS', 'GDPR,CCPA'),
            response_timeframe=int(os.getenv('RESPONSE_TIMEFRAME_DAYS', 30))
        )

    def validate(self):
        required_fields = ['user_name', 'user_email', 'website_name']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Missing required field: {field}")
        return self

class EmailStructure(TypedDict):
    subject: str
    greeting: str
    introduction: str
    main_content: str
    closing: str
    signature: str

class EmailTemplate:
    @staticmethod
    def get_structure() -> EmailStructure:
        return {
            "subject": "Personal Data Deletion Request - {website_name}",
            "greeting": "Dear {website_name} Data Protection Team,",
            "introduction": """
                I am writing to formally request the deletion of all my personal data 
                from your systems and records, in accordance with {privacy_law}.
            """,
            "main_content": """
                Personal Information:
                - Name: {user_name}
                - Email: {user_email}

                Specific Requests:
                1. Complete deletion of all my personal data from your active systems
                2. Removal of my information from any backup systems
                3. Confirmation of deletion once completed

                Please provide confirmation of receipt of this request and an expected 
                timeframe for completion. According to {privacy_law}, I expect to receive 
                a response within {response_timeframe} days.
            """,
            "closing": """
                If you require any additional information to verify my identity or process 
                this request, please let me know.

                Thank you for your attention to this matter.
            """,
            "signature": """
                Best regards,
                {user_name}
            """
        }

    @staticmethod
    def get_guidelines() -> str:
        return """
        Email Guidelines:
        1. Maintain professional tone throughout
        2. Be clear and concise
        3. Include all necessary legal references
        4. Request explicit confirmation
        5. Set clear expectations for response
        6. Include all required personal identifiers
        """ 