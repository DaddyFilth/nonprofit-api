from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Text
from app.db import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)

    # Location info
    location_city = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)

    raw_url = Column(String)
    posted_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)

    status = Column(String, default="available") # available, claimed, distributed

    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
