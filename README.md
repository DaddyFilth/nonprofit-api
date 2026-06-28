# Nonprofit API & AI Assistant

This project combines a FastAPI-based management system for nonprofits with a RAG-powered AI Assistant.

## Project Structure

- `app/`: FastAPI application (Models, Routers, Services).
- `rag/`: AI Assistant and Codebase RAG logic.
- `scrapers/`: Scripts for ingesting data from external sources.
- `chroma_db/`: Local vector store for codebase indexing.

## Features

- **Donor Management**: Track engagement and contributions.
- **Automated Receipts**: Generate and email PDF receipts.
- **Reporting & Analytics**: Financial and inventory dashboards.
- **AI Assistant**: A RAG-powered agent that understands the codebase and can answer developer queries.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (`.env`):
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
   OPENAI_API_KEY=your_key
   INGEST_TOKEN=your_api_token
   ```

3. Index the codebase (for the AI Assistant):
   ```bash
   python -m rag.indexer
   ```

4. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Run the AI Assistant:
   ```bash
   python -m rag.assistant
   ```

## Scraper Automation

The project includes an orchestrator to run multiple scrapers and ingest data into the API.

1. Run all scrapers manually:
   ```bash
   python scrapers/orchestrator.py
   ```

2. Local Automation (Cron):
   To run scrapers every hour, add this to your `crontab -e`:
   ```bash
   0 * * * * cd /path/to/nonprofit-api && ./venv/bin/python scrapers/orchestrator.py >> scraper_cron.log 2>&1
   ```

3. Integrated Scheduler:
   The app has a built-in scheduler. Enable it with `ENABLE_SCHEDULER=true`. See [Automation Alternatives](docs/automation-alternatives.md) for details.

4. Systemd Timers (Linux):
   For a more robust Linux-native automation, see the Systemd guide in [Automation Alternatives](docs/automation-alternatives.md).
