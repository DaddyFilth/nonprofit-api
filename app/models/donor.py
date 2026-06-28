from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

# Import for type hints (avoid circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.donation import Donation

class Donor(Base):
    __tablename__ = "donors"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    phone = Column(String)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    
    # Engagement tracking
    total_donations = Column(Integer, default=0)
    total_value = Column(Integer, default=0)  # in cents
    first_donation_date = Column(DateTime)
    last_donation_date = Column(DateTime)
    
    # Communication preferences
    email_opt_in = Column(Boolean, default=True)
    sms_opt_in = Column(Boolean, default=False)
    
    # Metadata
    tags = Column(Text)  # JSON array of tags
    notes = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    donations = relationship("Donation", back_populates="donor", cascade="all, delete-orphan")