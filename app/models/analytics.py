from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, Float, JSON
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"
    
    id = Column(String, primary_key=True)
    cache_key = Column(String, unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    computed_at = Column(DateTime, default=get_utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    def is_expired(self) -> bool:
        return get_utc_now() > self.expires_at

class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # 'donor_summary', 'financial', 'inventory'
    frequency = Column(String, nullable=False)   # 'daily', 'weekly', 'monthly'
    recipients = Column(JSON, nullable=False)     # List of email addresses
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime, nullable=False)
    is_active = Column(Integer, default=1)  # Boolean as integer
    parameters = Column(JSON)  # Additional report parameters
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)