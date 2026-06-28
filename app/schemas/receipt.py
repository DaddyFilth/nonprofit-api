from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReceiptBase(BaseModel):
    donor_id: str
    donation_id: Optional[str] = None
    amount: int
    donation_date: datetime
    tax_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_address: Optional[str] = None

class ReceiptCreate(ReceiptBase):
    pass

class ReceiptResponse(ReceiptBase):
    id: str
    receipt_number: str
    receipt_date: datetime
    status: str
    pdf_path: Optional[str] = None
    email_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReceiptResendRequest(BaseModel):
    email: Optional[str] = None  # Override donor email if provided