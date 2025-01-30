from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class WebsiteData(BaseModel):
    """Output schema for website scraping task"""
    contact_emails: List[str] = Field(default_factory=list, description="Discovered email addresses")
    privacy_policies: Dict[str, str] = Field(default_factory=dict, description="Privacy policy URLs and content")
    deletion_procedures: str = Field("", description="Data deletion request procedures")
    contact_forms: List[str] = Field(default_factory=list, description="Contact form URLs")
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalysisReport(BaseModel):
    """Output schema for content analysis task"""
    recommended_contact: str = Field(..., description="Primary contact method")
    privacy_excerpts: List[str] = Field(default_factory=list, description="Relevant privacy policy sections")
    deletion_requirements: List[str] = Field(default_factory=list, description="Requirements for deletion requests")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance considerations")
    timestamp: datetime = Field(default_factory=datetime.now)

class DeletionRequest(BaseModel):
    """Output schema for deletion request composition"""
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    html_version: Optional[str] = Field(None, description="HTML formatted version")
    legal_basis: str = Field(..., description="Legal basis for request")
    timestamp: datetime = Field(default_factory=datetime.now)

class EmailConfirmation(BaseModel):
    """Output schema for email sending task"""
    message_id: str = Field(..., description="Email message ID")
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    sent_timestamp: datetime = Field(default_factory=datetime.now)
    delivery_status: str = Field(..., description="Delivery status")

class ResponseAnalysis(BaseModel):
    """Output schema for response monitoring"""
    responses: List[Dict] = Field(default_factory=list, description="List of responses received")
    confirmation_status: str = Field(..., description="Overall confirmation status")
    required_actions: List[str] = Field(default_factory=list, description="Required follow-up actions")
    compliance_status: str = Field(..., description="Compliance assessment")
    last_check: datetime = Field(default_factory=datetime.now)

class ManagerDecision(BaseModel):
    """Output schema for manager review"""
    process_status: str = Field(..., description="Overall process status")
    response_summary: str = Field(..., description="Summary of responses")
    compliance_assessment: str = Field(..., description="Compliance assessment")
    follow_up_actions: List[str] = Field(default_factory=list, description="Required follow-up actions")
    timeline: Dict[str, datetime] = Field(default_factory=dict, description="Process timeline")
    review_timestamp: datetime = Field(default_factory=datetime.now) 