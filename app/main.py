from typing import List, Optional
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, HttpUrl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from contextlib import asynccontextmanager
from .db import get_session, engine, Base
from .routers import donors, donations, receipts, analytics, ui
from .schemas.item import ItemIn
from .services.scheduler_service import SchedulerService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if using SQLite (for easy dev)
    if engine.url.drivername == "sqlite+aiosqlite":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Start the scraper scheduler
    scheduler = SchedulerService()
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    # Shutdown: Clean up scheduler
    scheduler.shutdown()

app = FastAPI(title="Nonprofit Ingest API", lifespan=lifespan)

# Include routers
app.include_router(ui.router)
app.include_router(donors.router)
app.include_router(donations.router)
app.include_router(receipts.router)
app.include_router(analytics.router)

security = HTTPBearer(auto_error=False)


def verify_token(creds: HTTPAuthorizationCredentials | None) -> None:
    import os

    expected = os.environ.get("INGEST_TOKEN")
    if not expected:
        # Deny access if INGEST_TOKEN is not configured (security by default)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingest token not configured on server",
        )
    if not creds or creds.scheme.lower() != "bearer" or creds.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/ingest-items", status_code=status.HTTP_202_ACCEPTED)
async def ingest_items(
    items: List[ItemIn],
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    verify_token(creds)

    if not items:
        return {"received": 0}

    stmt = text(
        """
        INSERT INTO items (
            id, source, title, description, category,
            location_city, location_lat, location_lon,
            raw_url, posted_at, expires_at, status
        )
        VALUES (
            :id, :source, :title, :description, :category,
            :location_city, :location_lat, :location_lon,
            :raw_url, :posted_at, :expires_at, 'available'
        )
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            location_city = EXCLUDED.location_city,
            location_lat = EXCLUDED.location_lat,
            location_lon = EXCLUDED.location_lon,
            raw_url = EXCLUDED.raw_url,
            posted_at = EXCLUDED.posted_at,
            expires_at = EXCLUDED.expires_at
        """
    )

    payloads = []
    for item in items:
        payloads.append(
            {
                "id": item.id,
                "source": item.source,
                "title": item.title,
                "description": item.description,
                "category": item.category,
                "location_city": item.location.city,
                "location_lat": item.location.lat,
                "location_lon": item.location.lon,
                "raw_url": str(item.raw_url) if item.raw_url else None,
                "posted_at": item.posted_at,
                "expires_at": item.expires_at,
            }
        )

    async with session.begin():
        for row in payloads:
            await session.execute(stmt, row)

    return {"received": len(items)}
