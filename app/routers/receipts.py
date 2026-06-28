from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from app.db import get_session
from app.schemas.receipt import ReceiptCreate, ReceiptResponse, ReceiptResendRequest
from app.models.receipt import Receipt
from app.services.receipt_generator import ReceiptGenerator
from app.services.email_service import EmailService
from app.services.donor_service import DonorService

router = APIRouter(prefix="/receipts", tags=["receipts"])

@router.post("/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
    receipt_data: ReceiptCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    donor_service = DonorService(session)
    receipt_generator = ReceiptGenerator()
    email_service = EmailService()
    
    # Get donor
    donor = await donor_service.get_donor(receipt_data.donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    # Generate receipt
    receipt_number = receipt_generator.generate_receipt_number()
    organization_info = {
        "name": receipt_data.organization_name or "Nonprofit Organization",
        "address": receipt_data.organization_address or "",
        "tax_id": receipt_data.tax_id or ""
    }
    
    # Create receipt record
    receipt = Receipt(
        id=str(uuid.uuid4()),
        receipt_number=receipt_number,
        **receipt_data.model_dump()
    )
    
    # Generate PDF
    pdf_path = await receipt_generator.generate_pdf(receipt, donor, organization_info)
    receipt.pdf_path = pdf_path
    receipt.status = "generated"
    
    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    
    # Send email in background
    background_tasks.add_task(
        email_service.send_receipt_email,
        to_email=donor.email,
        donor_name=donor.name or "Valued Donor",
        receipt_number=receipt_number,
        pdf_path=pdf_path,
        amount=receipt.amount / 100
    )
    
    return receipt

@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(receipt_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

@router.get("/", response_model=List[ReceiptResponse])
async def list_receipts(
    donor_id: str = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    query = select(Receipt)
    if donor_id:
        query = query.where(Receipt.donor_id == donor_id)
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()

@router.post("/{receipt_id}/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_receipt(
    receipt_id: str,
    resend_data: ReceiptResendRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    donor_service = DonorService(session)
    donor = await donor_service.get_donor(receipt.donor_id)
    
    email_service = EmailService()
    email_to = resend_data.email or donor.email
    
    background_tasks.add_task(
        email_service.send_receipt_email,
        to_email=email_to,
        donor_name=donor.name or "Valued Donor",
        receipt_number=receipt.receipt_number,
        pdf_path=receipt.pdf_path,
        amount=receipt.amount / 100
    )
    
    return {"message": "Receipt resend queued"}