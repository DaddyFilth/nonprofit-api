import os
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import AsyncSessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.donor_service import DonorService
from app.services.auth_service import AuthService
from app.schemas.analytics import DashboardMetrics

router = APIRouter(prefix="", tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return RedirectResponse(url="/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    user = await AuthService.get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(
        request=request,
        name="dashboard/login.html",
        context={"error": error}
    )

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "password")

    # Simple check: plain text for dev default, hash for production env var
    is_valid = False
    if username == admin_user:
        if password == admin_pass:
            is_valid = True
        elif admin_pass.startswith("$2b$") and AuthService.verify_password(password, admin_pass):
            is_valid = True

    if is_valid:
        token = AuthService.create_access_token(data={"sub": username})
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response

    return RedirectResponse(url="/login?error=Invalid credentials", status_code=303)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    metrics = None
    try:
        async with AsyncSessionLocal() as session:
            analytics_service = AnalyticsService(session)
            metrics = await analytics_service.get_dashboard_metrics()
    except Exception as e:
        print(f"DATABASE ERROR in dashboard_home: {e}")

    if metrics is None:
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

    scheduler_active = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "metrics": metrics,
            "scheduler_active": scheduler_active,
            "user": user
        }
    )

@router.get("/dashboard/donors", response_class=HTMLResponse)
async def donor_view(request: Request):
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

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
            "donors": donors,
            "user": user
        }
    )

@router.get("/dashboard/scrapers", response_class=HTMLResponse)
async def scraper_view(request: Request):
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    scrapers = [
        {"name": "Craigslist Free", "interval": "60m"},
        {"name": "Craigslist Robot", "interval": "60m"},
        {"name": "Beta Electronics", "interval": "60m"},
        {"name": "Generic Free Crawler", "interval": "60m"}
    ]

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
            "logs": logs,
            "user": user
        }
    )

@router.post("/dashboard/scrapers/run")
async def trigger_scrapers(request: Request):
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    from scrapers.orchestrator import main as run_scrapers
    import asyncio
    asyncio.create_task(asyncio.to_thread(run_scrapers))
    return RedirectResponse(url="/dashboard/scrapers", status_code=303)
