from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Campaign details
    target_materials = Column(Text)  # JSON array of material types needed
    target_region = Column(String)  # geographic focus
    target_quantity = Column(Text)  # JSON object with material quantities
    
    # Campaign status
    status = Column(String, default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Outreach metrics
    total_suppliers_contacted = Column(Integer, default=0)
    positive_responses = Column(Integer, default=0)
    negative_responses = Column(Integer, default=0)
    pending_responses = Column(Integer, default=0)
    
    # Marketing materials
    generated_thank_you_email = Column(Text)
    generated_social_post = Column(Text)
    generated_press_release = Column(Text)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    suppliers = relationship("CampaignSupplier", back_populates="campaign", cascade="all, delete-orphan")

class CampaignSupplier(Base):
    __tablename__ = "campaign_suppliers"
    
    id = Column(String, primary_key=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    
    # Outreach status for this specific campaign
    status = Column(String, default="pending")  # pending, contacted, responded, interested, declined
    contact_date = Column(DateTime)
    response_date = Column(DateTime)
    
    # Response details
    response_notes = Column(Text)
    donation_commitment = Column(Text)  # JSON object with commitment details
    donation_value = Column(Integer)  # in cents
    
    # Marketing
    thank_you_sent = Column(Boolean, default=False)
    social_post_created = Column(Boolean, default=False)
    press_release_sent = Column(Boolean, default=False)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="campaigns")