from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_session
from app.schemas.donor import DonorCreate, DonorUpdate, DonorResponse
from app.services.donor_service import DonorService

router = APIRouter(prefix="/donors", tags=["donors"])

@router.post("/", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    donor_data: DonorCreate,
    session: AsyncSession = Depends(get_session)
):
    service = DonorService(session)
    
    # Check for existing email
    existing = await service.get_donor_by_email(donor_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    donor = await service.create_donor(donor_data)
    return donor

@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(donor_id: str, session: AsyncSession = Depends(get_session)):
    service = DonorService(session)
    donor = await service.get_donor(donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.get("/", response_model=List[DonorResponse])
async def list_donors(
    skip: int = 0,
    limit: int = 100,
    tags: str = None,
    session: AsyncSession = Depends(get_session)
):
    service = DonorService(session)
    tag_list = tags.split(",") if tags else None
    donors = await service.list_donors(skip=skip, limit=limit, tags=tag_list)
    return donors

@router.put("/{donor_id}", response_model=DonorResponse)
async def update_donor(
    donor_id: str,
    update_data: DonorUpdate,
    session: AsyncSession = Depends(get_session)
):
    service = DonorService(session)
    donor = await service.update_donor(donor_id, update_data)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donor(donor_id: str, session: AsyncSession = Depends(get_session)):
    service = DonorService(session)
    success = await service.delete_donor(donor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Donor not found")