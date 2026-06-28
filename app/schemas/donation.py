from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

DonationType = Literal["monetary", "in-kind", "recurring"]
DonationStatus = Literal["pending", "completed", "cancelled"]

class DonationBase(BaseModel):
    donor_id: str
    donation_type: DonationType = "monetary"
    amount: int
    description: Optional[str] = None
    item_id: Optional[str] = None
    item_description: Optional[str] = None
    item_category: Optional[str] = None
    notes: Optional[str] = None

class DonationCreate(DonationBase):
    generate_receipt: bool = False

class DonationUpdate(BaseModel):
    donation_type: Optional[DonationType] = None
    amount: Optional[int] = None
    description: Optional[str] = None
    status: Optional[DonationStatus] = None
    notes: Optional[str] = None

class DonationResponse(DonationBase):
    id: str
    status: DonationStatus
    donation_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True