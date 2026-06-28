from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import relationship
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    
    # Contact type
    contact_person = Column(String)
    contact_role = Column(String)  # e.g., "PR Manager", "Community Outreach"
    
    # Status tracking
    status = Column(String, default="new")  # new, contacted, interested, declined, donated
    last_contacted = Column(DateTime)
    response_received = Column(Boolean, default=False)
    
    # Outreach tracking
    contact_attempts = Column(Integer, default=0)
    last_outreach_method = Column(String)  # email, form, phone
    
    # Supplier details
    company_size = Column(String)  # small, medium, large, enterprise
    industry_focus = Column(Text)  # e.g., "lumber, concrete, roofing"
    notes = Column(Text)
    
    # Metadata
    tags = Column(Text)  # JSON array of tags
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    campaigns = relationship("CampaignSupplier", back_populates="supplier", cascade="all, delete-orphan")