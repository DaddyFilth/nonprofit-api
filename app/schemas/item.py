from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class LocationBase(BaseModel):
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class ItemBase(BaseModel):
    id: str
    source: str
    title: str
    description: str = ""
    category: str
    raw_url: Optional[HttpUrl] = None
    posted_at: datetime
    expires_at: Optional[datetime] = None

class ItemIn(ItemBase):
    location: LocationBase

class ItemResponse(ItemBase):
    location_city: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
