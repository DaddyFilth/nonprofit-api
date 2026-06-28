import os
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.donor_service import DonorService
from app.schemas.analytics import DashboardMetrics

router = APIRouter(prefix="", tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return RedirectResponse(url="/dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    metrics = None
    try:
        async with AsyncSessionLocal() as session:
            analytics_service = AnalyticsService(session)
            metrics = await analytics_service.get_dashboard_metrics()
    except Exception as e:
        print(f"DATABASE ERROR in dashboard_home: {e}")

    if metrics is None:
        # Return empty metrics on DB failure to avoid 500 error
        metrics = DashboardMetrics(
            total_donors=0,
            active_donors=0,
            total_donations=0,
            total_revenue=0.0,
            avg_donation_amount=0.0,
            items_collected=0,
            items_distributed=0,
            revenue_this_month=0.0,
            revenue_this_year=0.0,
            donor_retention_rate=0.0
        )

    # Check if scheduler is running via app state
    scheduler_active = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "metrics": metrics,
            "scheduler_active": scheduler_active
        }
    )

@router.get("/dashboard/donors", response_class=HTMLResponse)
async def donor_view(request: Request):
    try:
        async with AsyncSessionLocal() as session:
            service = DonorService(session)
            donors = await service.list_donors()
    except Exception as e:
        print(f"Error fetching donors: {e}")
        donors = []

    return templates.TemplateResponse(
        request=request,
        name="dashboard/donors.html",
        context={
            "donors": donors
        }
    )

@router.get("/dashboard/scrapers", response_class=HTMLResponse)
async def scraper_view(request: Request):
    scrapers = [
        {"name": "Craigslist Free", "interval": "60m"},
        {"name": "Craigslist Robot", "interval": "60m"},
        {"name": "Beta Electronics", "interval": "60m"},
        {"name": "Generic Free Crawler", "interval": "60m"}
    ]

    # Read the latest logs
    try:
        with open("scrapers.log", "r") as f:
            logs = "".join(f.readlines()[-20:])
    except FileNotFoundError:
        logs = "No logs available."

    return templates.TemplateResponse(
        request=request,
        name="dashboard/scrapers.html",
        context={
            "scrapers": scrapers,
            "logs": logs
        }
    )

@router.post("/dashboard/scrapers/run")
async def trigger_scrapers():
    from scrapers.orchestrator import main as run_scrapers
    import asyncio
    # Run in background to not block the UI
    asyncio.create_task(asyncio.to_thread(run_scrapers))
    return RedirectResponse(url="/dashboard/scrapers", status_code=303)
