from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

# Import for type hints (avoid circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.donor import Donor

class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(String, primary_key=True)
    donor_id = Column(String, ForeignKey("donors.id"), nullable=False)
    
    # Donation details
    donation_type = Column(String, default="monetary")
    amount = Column(Integer, nullable=False)  # in cents
    description = Column(Text)
    
    # Item details for in-kind donations
    item_id = Column(String)  # Reference to items table
    item_description = Column(Text)
    item_category = Column(String)
    
    # Status tracking
    status = Column(String, default="pending")
    donation_date = Column(DateTime, default=get_utc_now)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    donor = relationship("Donor", back_populates="donations")