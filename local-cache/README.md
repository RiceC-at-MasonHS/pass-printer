# Smartpass Schedule Scraper

Side-car utility for `pass-printer`. Automates student schedule extraction from Smartpass.

## Installation

1. **Prerequisites**: Python 3.x, Debian/Ubuntu server.
2. **Run Installer**:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```
3. **Configure**:
   Edit `/opt/schedule-scraper/.env`:
   ```env
   CLEVER_USERNAME=your_username
   CLEVER_PASSWORD=your_password
   SCHOOL_ID=2844
   SCRAPER_MODE=dev  # 'dev' for 5 students, 'prod' for full school
   ```

## Architecture

- **Path**: `/opt/schedule-scraper`
- **Database**: `/opt/pass-printer/data.db` (Shared)
- **Service**: `schedule-scraper.service`
- **Timer**: `schedule-scraper.timer` (Runs daily at 3:00 AM)

## Components

- `smartpass_scraper.py`: Main logic for data extraction.
- `auth_clever.py`: Automated headless login via Playwright.
- `SCHEMA.md`: Database documentation for integration.

## Manual Triggers

### 1. Command Line (Recommended)
Trigger a sync via systemd:
```bash
sudo systemctl start schedule-scraper.service
```

### 2. Local Web API (Delayed Starts)
A local API runs on port `48273` for manual triggers (e.g., via a local script or curl on the server):
- **Trigger Sync**: `curl -X POST http://127.0.0.1:48273/sync`
- **Check Status**: `curl http://127.0.0.1:48273/stats`

*Note: The API is bound to 127.0.0.1 and is not reachable from the network.*
