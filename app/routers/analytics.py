from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from app.db import get_session
from app.schemas.analytics import (
    DashboardMetrics, DonorAnalytics, FinancialSummary,
    InventoryReport, ReportCreate, ReportResponse
)
from app.services.analytics_service import AnalyticsService

from fastapi.responses import Response

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    return await service.get_dashboard_metrics(start_date, end_date)

@router.get("/donors/{donor_id}", response_model=DonorAnalytics)
async def get_donor_analytics(
    donor_id: str,
    session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    analytics = await service.get_donor_analytics(donor_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Donor not found")
    return analytics

@router.get("/financial", response_model=FinancialSummary)
async def get_financial_summary(
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    return await service.get_financial_summary(start_date, end_date)

@router.get("/inventory", response_model=InventoryReport)
async def get_inventory_report(
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    return await service.get_inventory_report(start_date, end_date)

@router.get("/export/donations")
async def export_donations(
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession = Depends(get_session)
):
    service = AnalyticsService(session)
    csv_data = await service.get_donations_report(start_date, end_date)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=donations_{start_date.date()}_{end_date.date()}.csv"}
    )
