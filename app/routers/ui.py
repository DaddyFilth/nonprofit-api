import os
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="", tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return RedirectResponse(url="/dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request, session: AsyncSession = Depends(get_session)):
    analytics_service = AnalyticsService(session)
    metrics = await analytics_service.get_dashboard_metrics()

    # Check if scheduler is running via app state
    scheduler_active = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "metrics": metrics,
        "scheduler_active": scheduler_active
    })

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

    return templates.TemplateResponse("dashboard/scrapers.html", {
        "request": request,
        "scrapers": scrapers,
        "logs": logs
    })

@router.post("/dashboard/scrapers/run")
async def trigger_scrapers():
    from scrapers.orchestrator import main as run_scrapers
    import asyncio
    # Run in background to not block the UI
    asyncio.create_task(asyncio.to_thread(run_scrapers))
    return RedirectResponse(url="/dashboard/scrapers", status_code=303)
