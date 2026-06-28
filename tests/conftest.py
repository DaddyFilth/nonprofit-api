import os
from typing import AsyncIterator, Dict

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session", autouse=True)
def test_env() -> None:
    """Set safe defaults for tests via environment variables.

    - Disable the internal scheduler to avoid background jobs during tests.
    - Use local SQLite database file in project root.
    - Provide a deterministic ingest token for authenticated endpoints.
    - Leave outreach drafts disabled to avoid LLM calls.
    """
    os.environ["ENABLE_SCHEDULER"] = "false"
    os.environ["ENABLE_OUTREACH_DRAFTS"] = "false"
    os.environ["OUTREACH_DRAFT_INTERVAL"] = "240"
    os.environ["OUTREACH_DRAFT_DIR"] = "reports/outreach_drafts"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./nonprofit.db"
    os.environ["INGEST_TOKEN"] = "testtoken"
    # Optional LLM envs remain unset by default to prevent accidental calls


@pytest.fixture(scope="session")
def test_app():
    """Return the FastAPI app instance for ASGI testing."""
    from app.main import app

    return app


@pytest.fixture
async def client(test_app) -> AsyncIterator[AsyncClient]:
    """Shared async HTTP client bound to the FastAPI app.

    Uses ASGITransport with lifespan handling enabled so startup/shutdown
    events run properly (e.g., table creation when using SQLite).
    """
    transport = ASGITransport(app=test_app, lifespan="on")
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_header() -> Dict[str, str]:
    """Convenience fixture for Bearer auth header using INGEST_TOKEN from env."""
    token = os.environ.get("INGEST_TOKEN", "testtoken")
    return {"Authorization": f"Bearer {token}"}
