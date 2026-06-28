from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class DonorBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email_opt_in: bool = True
    sms_opt_in: bool = False
    tags: Optional[List[str]] = []
    notes: Optional[str] = None

class DonorCreate(DonorBase):
    pass

class DonorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email_opt_in: Optional[bool] = None
    sms_opt_in: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class DonorResponse(DonorBase):
    id: str
    total_donations: int
    total_value: int
    first_donation_date: Optional[datetime] = None
    last_donation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True