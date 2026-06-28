from typing import List, Optional
from pydantic import BaseModel, EmailStr


class MaterialItem(BaseModel):
    name: str
    use: Optional[str] = None


class OutreachGenerateRequest(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    project_context: Optional[str] = None
    materials: Optional[List[MaterialItem]] = None
    call_to_action: Optional[str] = None


class OutreachEmail(BaseModel):
    subject: str
    body: str


class OutreachSendRequest(OutreachGenerateRequest):
    to_email: EmailStr


class OutreachResponse(BaseModel):
    email: OutreachEmail
    sent: bool = False
    to_email: Optional[EmailStr] = None
