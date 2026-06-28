# Alternative Automation Options (No GitHub Actions)

If you prefer not to use GitHub Actions, here are two robust alternatives for automating your scrapers.

## Option 1: Integrated App Scheduler (Recommended for Portability)

The application now has **APScheduler** built-in. This runs the scrapers as a background thread within the FastAPI process.

### How to enable:
Set the following environment variables when running your app:
```bash
ENABLE_SCHEDULER=true
SCRAPER_INTERVAL=60  # minutes
```

Example:
```bash
ENABLE_SCHEDULER=true SCRAPER_INTERVAL=30 uvicorn app.main:app --reload
```

---

## Option 2: Systemd Timers (Recommended for Production/Linux)

Systemd timers are the modern Linux replacement for Cron. They provide better logging and resource management.

### 1. Create the Service File
Create `/etc/systemd/system/nonprofit-scraper.service`:
```ini
[Unit]
Description=Nonprofit Scraper Orchestrator
After=network.target

[Service]
Type=oneshot
User=filth
WorkingDirectory=/home/filth/StudioProjects/nonprofit-api
Environment="INGEST_API_BASE=http://localhost:8000"
Environment="INGEST_TOKEN=your_token_here"
ExecStart=/home/filth/StudioProjects/nonprofit-api/venv/bin/python scrapers/orchestrator.py
```

### 2. Create the Timer File
Create `/etc/systemd/system/nonprofit-scraper.timer`:
```ini
[Unit]
Description=Run Nonprofit Scraper every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Unit=nonprofit-scraper.service

[Install]
WantedBy=timers.target
```

### 3. Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nonprofit-scraper.timer
```

### 4. Check Status
```bash
systemctl list-timers --all
journalctl -u nonprofit-scraper.service
```
