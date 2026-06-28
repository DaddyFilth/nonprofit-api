from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.donation import Donation
from app.schemas.donation import DonationCreate, DonationUpdate
import uuid

class DonationService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_donation(self, donation_data: DonationCreate, generate_receipt: bool = False) -> Donation:
        donation = Donation(
            id=str(uuid.uuid4()),
            **donation_data.model_dump()
        )
        self.session.add(donation)
        await self.session.commit()
        await self.session.refresh(donation)
        
        # Update donor statistics
        from app.services.donor_service import DonorService
        donor_service = DonorService(self.session)
        await donor_service.update_donation_stats(donation.donor_id, donation.amount)

        if generate_receipt and donation.donation_type == "monetary":
            from app.services.receipt_generator import ReceiptGenerator
            from app.models.receipt import Receipt
            import uuid as uuid_pkg

            receipt_generator = ReceiptGenerator()
            donor = await donor_service.get_donor(donation.donor_id)

            receipt_number = receipt_generator.generate_receipt_number()
            receipt = Receipt(
                id=str(uuid_pkg.uuid4()),
                donor_id=donation.donor_id,
                donation_id=donation.id,
                receipt_number=receipt_number,
                amount=donation.amount,
                donation_date=donation.donation_date or datetime.now(),
                organization_name="Nonprofit Organization", # Should come from settings
                status="pending"
            )

            # Note: In a production app, this would be a background task
            # For simplicity here, we generate it inline or just create the record
            self.session.add(receipt)
            await self.session.commit()

        return donation
    
    async def get_donation(self, donation_id: str) -> Optional[Donation]:
        result = await self.session.execute(select(Donation).where(Donation.id == donation_id))
        return result.scalar_one_or_none()
    
    async def get_donations_by_donor(self, donor_id: str) -> List[Donation]:
        result = await self.session.execute(
            select(Donation).where(Donation.donor_id == donor_id)
        )
        return result.scalars().all()
    
    async def update_donation(self, donation_id: str, update_data: DonationUpdate) -> Optional[Donation]:
        donation = await self.get_donation(donation_id)
        if not donation:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(donation, field, value)
        
        await self.session.commit()
        await self.session.refresh(donation)
        return donation
    
    async def list_donations(self, skip: int = 0, limit: int = 100) -> List[Donation]:
        query = select(Donation).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_donation(self, donation_id: str) -> bool:
        donation = await self.get_donation(donation_id)
        if not donation:
            return False
        
        await self.session.delete(donation)
        await self.session.commit()
        return True