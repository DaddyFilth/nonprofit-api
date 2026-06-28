from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(String, primary_key=True)
    donor_id = Column(String, ForeignKey("donors.id"), nullable=False)
    donation_id = Column(String, ForeignKey("donations.id"), nullable=True)
    
    # Receipt details
    receipt_number = Column(String, unique=True, nullable=False, index=True)
    receipt_date = Column(DateTime, default=get_utc_now)
    amount = Column(Integer, nullable=False)  # in cents
    donation_date = Column(DateTime, nullable=False)
    
    # Legal compliance
    tax_id = Column(String)  # Organization tax ID
    organization_name = Column(String)
    organization_address = Column(Text)
    
    # Status tracking
    status = Column(String, default="pending")  # pending, generated, sent, failed
    pdf_path = Column(String)  # Path to generated PDF
    email_sent_at = Column(DateTime)
    email_error = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)