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
