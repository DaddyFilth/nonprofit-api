from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_session
from app.schemas.donation import DonationCreate, DonationUpdate, DonationResponse
from app.services.donation_service import DonationService

router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    donation_data: DonationCreate,
    session: AsyncSession = Depends(get_session)
):
    service = DonationService(session)
    donation = await service.create_donation(
        donation_data,
        generate_receipt=donation_data.generate_receipt
    )
    return donation

@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(donation_id: str, session: AsyncSession = Depends(get_session)):
    service = DonationService(session)
    donation = await service.get_donation(donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation

@router.get("/donor/{donor_id}", response_model=List[DonationResponse])
async def get_donations_by_donor(donor_id: str, session: AsyncSession = Depends(get_session)):
    service = DonationService(session)
    donations = await service.get_donations_by_donor(donor_id)
    return donations

@router.get("/", response_model=List[DonationResponse])
async def list_donations(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    service = DonationService(session)
    donations = await service.list_donations(skip=skip, limit=limit)
    return donations

@router.put("/{donation_id}", response_model=DonationResponse)
async def update_donation(
    donation_id: str,
    update_data: DonationUpdate,
    session: AsyncSession = Depends(get_session)
):
    service = DonationService(session)
    donation = await service.update_donation(donation_id, update_data)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation

@router.delete("/{donation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donation(donation_id: str, session: AsyncSession = Depends(get_session)):
    service = DonationService(session)
    success = await service.delete_donation(donation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Donation not found")