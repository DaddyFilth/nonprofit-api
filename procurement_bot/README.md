# Autonomous Material Procurement and Marketing Bot

A modular Python system for finding building material suppliers, automating outreach, tracking responses, and generating marketing content for donation acknowledgments.

## Features

- **Supplier Discovery**: Automated web search and scraping to find building material suppliers
- **Contact Extraction**: Intelligent extraction of emails, phone numbers, and contact forms
- **Email Outreach**: Automated personalized donation request emails with rate limiting
- **Response Tracking**: Inbox monitoring and response analysis
- **Marketing Generation**: AI-powered thank you emails, social media posts, and press releases
- **Database Management**: SQLite/PostgreSQL backend for tracking suppliers and campaigns
- **Security**: Environment-based configuration for all API keys

## Architecture

The bot consists of five main modules:

1. **Database Module** (`modules/database.py`): Manages suppliers and campaigns
2. **Search Module** (`modules/search.py`): Web search and contact extraction
3. **Email Module** (`modules/email.py`): Email automation and response monitoring
4. **Marketing Module** (`modules/marketing.py`): AI-powered marketing copy generation
5. **Orchestrator** (`orchestrator.py`): Main coordination script

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Email Configuration (Choose one)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Search API (Choose one)
SEARCH_PROVIDER=serpapi
SERPAPI_KEY=your_serpapi_key

# LLM Configuration (Choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
```

### 3. Initialize Database

The database will be automatically created on first run. To verify:

```bash
source venv/bin/activate
python -c "from app.db import engine; from app.models import Base; import asyncio; asyncio.run(Base.metadata.create_all(engine))"
```

## Usage

### Single Cycle Run

Run a single cycle of the procurement process:

```bash
python procurement_bot/orchestrator.py
```

This will:
1. Search for new suppliers
2. Send outreach emails
3. Check for responses
4. Generate marketing materials for interested suppliers

### Continuous Mode

Run the bot in continuous mode with 60-minute intervals:

```bash
python procurement_bot/orchestrator.py --continuous 60
```

### Custom Configuration

Modify the orchestrator settings in `procurement_bot/orchestrator.py`:

```python
# Configure material types and locations
self.material_types = ["lumber", "concrete", "roofing"]
self.locations = ["Midwest", "Chicago", "Detroit"]

# Configure limits
self.max_new_suppliers_per_cycle = 10
self.max_outreach_per_cycle = 5
```

## API Key Setup Guide

### Email Provider

**Option 1: SMTP (Gmail)**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: Google Account → Security → App Passwords
3. Use the App Password in `SMTP_PASSWORD`

**Option 2: SendGrid**
1. Create a free SendGrid account
2. Generate an API Key
3. Use the API Key in `SENDGRID_API_KEY`

### Search Provider

**Option 1: SerpApi**
1. Create account at https://serpapi.com/
2. Get your API key from the dashboard
3. Use the API Key in `SERPAPI_KEY`

**Option 2: Google Custom Search**
1. Create a Custom Search Engine at https://programmablesearch.google.com/
2. Enable API access in Google Cloud Console
3. Use the API Key and Search Engine ID

### LLM Provider

**Option 1: OpenAI**
1. Create account at https://platform.openai.com/
2. Generate API key
3. Use the API Key in `OPENAI_API_KEY`

**Option 2: Anthropic**
1. Create account at https://console.anthropic.com/
2. Generate API key
3. Use the API Key in `ANTHROPIC_API_KEY`

## Database Schema

### Suppliers Table
- `id`: Unique identifier
- `name`: Company name
- `email`: Contact email
- `website`: Company website
- `status`: new, contacted, interested, declined, donated
- `contact_attempts`: Number of outreach attempts
- `last_contacted`: Last contact timestamp
- `industry_focus`: Type of materials supplied

### Campaigns Table
- `id`: Unique identifier
- `name`: Campaign name
- `target_materials`: JSON array of material types
- `status`: draft, active, paused, completed
- Marketing generated content

### Campaign Suppliers Table
- Links suppliers to campaigns
- Tracks per-campaign outreach status
- Records donation commitments

## Rate Limiting

The bot includes built-in rate limiting:

- `MAX_EMAILS_PER_HOUR`: Maximum emails per hour (default: 20)
- `MAX_SEARCHES_PER_HOUR`: Maximum searches per hour (default: 30)
- `DELAY_BETWEEN_EMAILS`: Delay between emails in seconds (default: 60)

## Logging

Logs are written to both console and file:

- File: `procurement_bot.log` (configurable via `LOG_FILE`)
- Level: `INFO` (configurable via `LOG_LEVEL`)

## Security

- All API keys are loaded from environment variables
- No hardcoded credentials in the codebase
- `.env` file should never be committed to version control
- Add `.env` to `.gitignore`

## Testing

Test individual modules:

```bash
# Test database
python -c "from procurement_bot.modules.database import db_manager; import asyncio; asyncio.run(db_manager.create_supplier(name='Test', email='test@example.com'))"

# Test search
python -c "from procurement_bot.modules.search import supplier_searcher; import asyncio; asyncio.run(supplier_searcher.search_suppliers('lumber suppliers'))"

# Test email
python -c "from procurement_bot.modules.email import outreach_engine; import asyncio; asyncio.run(outreach_engine.send_donation_request('Test Co', 'test@example.com'))"

# Test marketing
python -c "from procurement_bot.modules.marketing import marketing_generator; import asyncio; asyncio.run(marketing_generator.generate_thank_you_email('Test Co'))"
```

## Troubleshooting

### Import Errors
Ensure you're running from the project root and the virtual environment is activated:
```bash
source venv/bin/activate
python procurement_bot/orchestrator.py
```

### Database Connection Issues
Check your `DATABASE_URL` in `.env`. For local development, SQLite is sufficient:
```bash
DATABASE_URL=sqlite+aiosqlite:///./nonprofit.db
```

### Email Sending Failures
- Verify SMTP credentials are correct
- Check if your email provider requires additional authentication
- Ensure `EMAIL_PROVIDER` is set correctly in `.env`

### Search API Errors
- Verify your API key is valid
- Check if you've exceeded rate limits
- Ensure `SEARCH_PROVIDER` is configured

### LLM Generation Failures
- Verify your LLM API key is valid
- Check if you have sufficient credits/usage
- The bot will fall back to template-based generation if no API is configured

## Best Practices

1. **Start Small**: Begin with low rate limits and increase gradually
2. **Monitor Responses**: Regularly check the database for supplier responses
3. **Manual Review**: Always manually review generated marketing materials before publishing
4. **Compliance**: Ensure your outreach complies with anti-spam laws (CAN-SPAM, GDPR)
5. **Personalization**: Customize email templates for better response rates

## License

This project is part of the nonprofit-api system.

## Support

For issues or questions, please refer to the main project documentation.