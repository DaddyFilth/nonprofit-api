from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.models.donor import Donor
from app.schemas.donor import DonorCreate, DonorUpdate
import json
import uuid

def get_utc_now():
    return datetime.now(timezone.utc)

class DonorService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_donor(self, donor_data: DonorCreate) -> Donor:
        donor = Donor(
            id=str(uuid.uuid4()),
            **donor_data.model_dump()
        )
        donor.tags = json.dumps(donor_data.tags)
        self.session.add(donor)
        await self.session.commit()
        await self.session.refresh(donor)
        return donor
    
    async def get_donor(self, donor_id: str) -> Optional[Donor]:
        result = await self.session.execute(select(Donor).where(Donor.id == donor_id))
        return result.scalar_one_or_none()
    
    async def get_donor_by_email(self, email: str) -> Optional[Donor]:
        result = await self.session.execute(select(Donor).where(Donor.email == email))
        return result.scalar_one_or_none()
    
    async def update_donor(self, donor_id: str, update_data: DonorUpdate) -> Optional[Donor]:
        donor = await self.get_donor(donor_id)
        if not donor:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "tags" and value is not None:
                donor.tags = json.dumps(value)
            else:
                setattr(donor, field, value)
        
        await self.session.commit()
        await self.session.refresh(donor)
        return donor
    
    async def list_donors(self, skip: int = 0, limit: int = 100, tags: Optional[List[str]] = None) -> List[Donor]:
        query = select(Donor)
        
        if tags:
            # Simple tag filtering - in production, use proper JSON queries
            query = query.where(Donor.tags.like(f"%{tags[0]}%"))
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_donors(self, search_term: str) -> List[Donor]:
        search_pattern = f"%{search_term}%"
        query = select(Donor).where(
            or_(
                Donor.name.ilike(search_pattern),
                Donor.email.ilike(search_pattern),
                Donor.phone.ilike(search_pattern)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_donor(self, donor_id: str) -> bool:
        donor = await self.get_donor(donor_id)
        if not donor:
            return False
        
        await self.session.delete(donor)
        await self.session.commit()
        return True
    
    async def update_donation_stats(self, donor_id: str, amount: int) -> Donor:
        """Update donor statistics after a donation"""
        donor = await self.get_donor(donor_id)
        if not donor:
            raise ValueError("Donor not found")
        
        donor.total_donations += 1
        donor.total_value += amount
        
        if donor.first_donation_date is None:
            donor.first_donation_date = get_utc_now()
        donor.last_donation_date = get_utc_now()
        
        await self.session.commit()
        await self.session.refresh(donor)
        return donor