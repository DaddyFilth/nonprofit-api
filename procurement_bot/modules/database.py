"""
Database module for the procurement bot.

Handles database operations for suppliers and campaigns.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import AsyncSessionLocal
from app.models.supplier import Supplier
from app.models.campaign import Campaign, CampaignSupplier


class DatabaseManager:
    """Manages database operations for suppliers and campaigns."""
    
    def __init__(self):
        self.session_factory = AsyncSessionLocal
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async with self.session_factory() as session:
            yield session
    
    async def create_supplier(
        self,
        name: str,
        email: Optional[str] = None,
        website: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_role: Optional[str] = None,
        company_size: Optional[str] = None,
        industry_focus: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Supplier:
        """Create a new supplier."""
        import uuid
        
        async with self.session_factory() as session:
            supplier = Supplier(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                website=website,
                phone=phone,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                contact_person=contact_person,
                contact_role=contact_role,
                company_size=company_size,
                industry_focus=industry_focus,
                notes=notes,
                tags=tags,
                status="new",
            )
            session.add(supplier)
            await session.commit()
            await session.refresh(supplier)
            return supplier
    
    async def get_supplier_by_email(self, email: str) -> Optional[Supplier]:
        """Get a supplier by email address."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Supplier).where(Supplier.email == email)
            )
            return result.scalar_one_or_none()
    
    async def get_supplier_by_website(self, website: str) -> Optional[Supplier]:
        """Get a supplier by website."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Supplier).where(Supplier.website == website)
            )
            return result.scalar_one_or_none()
    
    async def get_suppliers_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Supplier]:
        """Get suppliers by status."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Supplier)
                .where(Supplier.status == status)
                .limit(limit)
            )
            return result.scalars().all()
    
    async def update_supplier_status(
        self,
        supplier_id: str,
        status: str,
        last_contacted: Optional[datetime] = None,
        response_received: bool = False,
        contact_attempts: Optional[int] = None,
        last_outreach_method: Optional[str] = None,
    ) -> Optional[Supplier]:
        """Update supplier status and tracking information."""
        async with self.session_factory() as session:
            update_data = {
                "status": status,
                "response_received": response_received,
            }
            
            if last_contacted:
                update_data["last_contacted"] = last_contacted
            if contact_attempts is not None:
                update_data["contact_attempts"] = contact_attempts
            if last_outreach_method:
                update_data["last_outreach_method"] = last_outreach_method
            
            result = await session.execute(
                update(Supplier)
                .where(Supplier.id == supplier_id)
                .values(**update_data)
                .returning(Supplier)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    async def create_campaign(
        self,
        name: str,
        description: Optional[str] = None,
        target_materials: Optional[str] = None,
        target_region: Optional[str] = None,
        target_quantity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Campaign:
        """Create a new campaign."""
        import uuid
        
        async with self.session_factory() as session:
            campaign = Campaign(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                target_materials=target_materials,
                target_region=target_region,
                target_quantity=target_quantity,
                start_date=start_date,
                end_date=end_date,
                notes=notes,
                status="draft",
            )
            session.add(campaign)
            await session.commit()
            await session.refresh(campaign)
            return campaign
    
    async def add_supplier_to_campaign(
        self,
        campaign_id: str,
        supplier_id: str,
    ) -> CampaignSupplier:
        """Add a supplier to a campaign."""
        import uuid
        
        async with self.session_factory() as session:
            # Check if already exists
            existing = await session.execute(
                select(CampaignSupplier).where(
                    and_(
                        CampaignSupplier.campaign_id == campaign_id,
                        CampaignSupplier.supplier_id == supplier_id
                    )
                )
            )
            existing_relation = existing.scalar_one_or_none()
            
            if existing_relation:
                return existing_relation
            
            campaign_supplier = CampaignSupplier(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                supplier_id=supplier_id,
                status="pending",
            )
            session.add(campaign_supplier)
            await session.commit()
            await session.refresh(campaign_supplier)
            return campaign_supplier
    
    async def get_campaign_suppliers(
        self,
        campaign_id: str,
        status: Optional[str] = None,
    ) -> List[CampaignSupplier]:
        """Get suppliers for a campaign, optionally filtered by status."""
        async with self.session_factory() as session:
            query = (
                select(CampaignSupplier)
                .options(selectinload(CampaignSupplier.supplier))
                .where(CampaignSupplier.campaign_id == campaign_id)
            )
            
            if status:
                query = query.where(CampaignSupplier.status == status)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_campaign_supplier_status(
        self,
        campaign_supplier_id: str,
        status: str,
        response_notes: Optional[str] = None,
        donation_commitment: Optional[str] = None,
        donation_value: Optional[int] = None,
    ) -> Optional[CampaignSupplier]:
        """Update campaign supplier status and response information."""
        async with self.session_factory() as session:
            update_data = {"status": status}
            
            if response_notes:
                update_data["response_notes"] = response_notes
            if donation_commitment:
                update_data["donation_commitment"] = donation_commitment
            if donation_value is not None:
                update_data["donation_value"] = donation_value
            
            if status in ["responded", "interested", "declined"]:
                update_data["response_date"] = datetime.now(timezone.utc)
            
            result = await session.execute(
                update(CampaignSupplier)
                .where(CampaignSupplier.id == campaign_supplier_id)
                .values(**update_data)
                .returning(CampaignSupplier)
            )
            await session.commit()
            return result.scalar_one_or_none()
    
    async def get_active_campaign(self) -> Optional[Campaign]:
        """Get the currently active campaign."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Campaign)
                .where(Campaign.status == "active")
                .order_by(Campaign.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_suppliers_ready_for_outreach(
        self,
        campaign_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get suppliers ready for outreach in a campaign."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(CampaignSupplier)
                .options(selectinload(CampaignSupplier.supplier))
                .where(
                    and_(
                        CampaignSupplier.campaign_id == campaign_id,
                        CampaignSupplier.status == "pending",
                        Supplier.status.in_(["new", "contacted"])
                    )
                )
                .limit(limit)
            )
            campaign_suppliers = result.scalars().all()
            
            return [
                {
                    "campaign_supplier_id": cs.id,
                    "supplier": cs.supplier,
                    "campaign_id": cs.campaign_id,
                }
                for cs in campaign_suppliers
            ]


# Singleton instance
db_manager = DatabaseManager()