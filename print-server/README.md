# Print Server

The **Print Server** is the core component of the pass-printer system. It receives late-arrival attendance data and orchestrates the printing of physical hall passes on a USB-connected POS thermal printer.

## Overview

The print server is a Flask-based Python application that:

1. **Receives** attendance data via HTTP (student name, timestamp, reason for being late)
2. **Queries** the local SQLite cache database to fetch the student's current class schedule
3. **Formats** pass content for thermal printer output
4. **Manages** a print queue with retry logic to handle printer failures
5. **Restricts** printing to school hours only and requires authentication

## Architecture

```
[Google Apps Script]
        ↓
    [HTTP Request]
        ↓
  [Flask Server] ←→ [SQLite Database]
        ↓                 ↑
  [Print Queue]      [Local Cache]
        ↓                 
  [USB Printer]
```

### Key Components

| Component | Purpose |
| --- | --- |
| **app.py** | Flask application with HTTP endpoints |
| **print_queue.py** | Print job management and thermal printer interface |
| **config.py** | Environment-based configuration loader |
| **requirements.txt** | Python dependencies |

## Features

### 🔐 Security
- **Bearer Token Authentication:** All print requests require a valid API passkey
- **School Hours Enforcement:** Printing is restricted to configured school hours (Mon-Fri only)
- **Rate Limiting:** Print queue has a 50-job limit to prevent attacks

### 🔄 Reliability
- **Automatic Retry Logic:** Failed print jobs are automatically re-queued (configurable max retries)
- **Background Processing:** Print jobs are processed by a dedicated worker thread
- **Job Status Tracking:** Query the status of any print job by ID

### 🎓 Student Schedule Integration
- **Database Lookup:** Automatically fetches current class info from local cache using `student_id`
- **Schedule Query:** Uses fuzzy logic to find the current or next class (handles passing periods)
- **Real-Time Data:** Pulls from SQLite cache maintained by the local-cache component

### 🖨️ Printer Support
- **USB POS Thermal Printer:** Supports standard Point-of-Sale thermal printers
- **Configurable:** Vendor and Product IDs can be customized for different printer models
- **ESC/POS Format:** Uses python-escpos library for formatted output

## Setup & Installation

### Prerequisites
- Python 3.7+
- Raspberry Pi (or any Linux system) with USB ports
- USB-connected thermal POS printer
- SQLite database from the local-cache component at `/opt/pass-printer/data.db`

### Installation Steps

1. **Clone or Copy Repository**
   ```bash
   git clone https://github.com/RiceC-at-MasonHS/pass-printer.git
   cd pass-printer/print-server
   ```

2. **Create Virtual Environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your specific values (see Configuration section below)

5. **Find Printer USB IDs** (if using a different printer)
   ```bash
   lsusb
   ```
   Look for your printer in the output and note the vendor:product IDs

6. **Run the Server**
   ```bash
   python app.py
   ```
   
   The server will start at `http://localhost:5000` (or your configured host/port)

## Configuration

All settings are configured via environment variables in `.env`:

### School Configuration
```env
SCHOOL_NAME_LINE_1=MASON HIGH          # First line of school name on pass
SCHOOL_NAME_LINE_2=SCHOOL              # Second line of school name on pass
SERVICE_NAME=Mason HS Hall Pass Server # Service identifier for logging
TIMEZONE=US/Eastern                     # Timezone for school hours
SCHOOL_START_HOUR=7                    # School start hour (24-hour format)
SCHOOL_START_MINUTE=30                 # School start minute
SCHOOL_END_HOUR=14                     # School end hour (14 = 2 PM)
SCHOOL_END_MINUTE=30                   # School end minute
```

### Database Configuration
```env
DB_NAME=data.db  # Path to SQLite database with student schedules
```

### Security Configuration
```env
PRINT_PASSKEY=your-super-secret-passkey-here  # Required for all print requests
```

### Printer Configuration
```env
PRINTER_VENDOR_ID=0x0483    # USB Vendor ID (hexadecimal)
PRINTER_PRODUCT_ID=0x5743   # USB Product ID (hexadecimal)
```

### Print Queue Configuration
```env
PRINT_MAX_RETRIES=5         # Max attempts before marking job as failed
PRINT_RETRY_DELAY=5         # Seconds between retry attempts
```

### Server Configuration
```env
SERVER_HOST=0.0.0.0         # Listen on all interfaces
SERVER_PORT=5000            # Flask server port
DEBUG=False                  # Enable Flask debug mode (false in production)
```

## API Endpoints

### `GET /health`
Health check endpoint to verify the server is running.

**Response:**
```json
{
  "status": "ok",
  "service": "Mason HS Hall Pass Server"
}
```

### `POST /print`
Submit a new print job. Requires authentication and school hours validation.

**Headers:**
```
Authorization: Bearer <PRINT_PASSKEY>
Content-Type: application/json
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "timestamp": "2024-05-16T09:15:00Z",
  "late_reason": "Traffic",
  "student_id": "123456"
}
```

**Response (202 Accepted):**
```json
{
  "status": "queued",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Pass queued for printing. Check status with /status/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400 Bad Request` - No JSON body provided
- `401 Unauthorized` - Missing or invalid passkey
- `403 Forbidden` - Outside school hours or weekend
- `500 Internal Server Error` - Printer not found or other server error

### `GET /status/<job_id>`
Check the status of a specific print job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-05-16T09:15:00.123456",
  "attempts": 1,
  "status": "completed",
  "error_message": null,
  "student": "John Doe"
}
```

**Possible Status Values:**
- `queued` - Waiting to be processed
- `processing` - Currently printing
- `completed` - Successfully printed
- `failed` - Failed after max retries

### `GET /queue`
Get overall print queue statistics and recent jobs.

**Response:**
```json
{
  "queued": 2,
  "processing": 1,
  "completed": 45,
  "failed": 0,
  "recent_jobs": [
    {
      "job_id": "...",
      "created_at": "...",
      "attempts": 1,
      "status": "completed",
      "error_message": null,
      "student": "John Doe"
    }
  ]
}
```

## Print Output Format

The thermal printer generates a pass in the following format:

```
        MASON HIGH
        SCHOOL
    LATE ARRIVAL PASS
    ════════════════════════
    John Doe
    ────────────────────────────────────────────────
    Time In: May 16, 2024  09:15 AM
    Reason : Traffic
    ────────────────────────────────────────────────
    SHOULD BE IN
    Period : Period 1 (Mon/Fri days)
    Class  : AP Chemistry
    Room   : C209
    Teacher: Ms. Johnson
    Until  : 08:31
    ════════════════════════════════════════════════
    Proceed directly to class.
    Hand this pass to your teacher.
```

## Data Flow

1. **Request arrives:** Google Apps Script sends POST to `/print` with student data and unique `student_id`
2. **Authentication:** Server validates the bearer token
3. **Time validation:** Server checks if it's school hours (Mon-Fri, 7:30 AM - 2:30 PM ET)
4. **Job creation:** A `PrintJob` is created and added to the queue
5. **Database lookup:** Worker thread queries SQLite for the student's current schedule using `student_id`
6. **Formatting:** Pass content is formatted with student info, current time, reason, and class schedule
7. **Printing:** Formatted content is sent to the USB thermal printer via ESC/POS protocol
8. **Status update:** Job status is updated to `completed` or `failed`

## Troubleshooting

### Printer Not Found
**Error:** `Printer connection error: Printer not found/unavailable`

**Solutions:**
1. Verify printer is connected via USB: `lsusb | grep printer-name`
2. Check PRINTER_VENDOR_ID and PRINTER_PRODUCT_ID in `.env`
3. Ensure user has permissions to access USB device: `sudo usermod -a -G lp $(whoami)`
4. Restart the server after permission changes

### Database Connection Error
**Error:** `sqlite3.OperationalError: unable to open database file`

**Solutions:**
1. Verify DB_NAME path exists and is readable
2. Check that the local-cache component has populated the database
3. Ensure the database file has read permissions: `chmod 644 /opt/pass-printer/data.db`

### Jobs Stuck in "Processing"
**Symptom:** Print jobs never complete

**Solutions:**
1. Check printer power and USB connection
2. Clear the printer paper jam if present
3. Restart the server to reset the worker thread
4. Check server logs for detailed error messages

### Authentication Failures
**Error:** `Invalid passkey` (401 Unauthorized)

**Solutions:**
1. Verify PRINT_PASSKEY is set in `.env`
2. Ensure the Google Apps Script is sending the correct bearer token
3. Check for whitespace or typos in the passkey

### Outside School Hours Errors
**Error:** `Printing disabled on weekends` (403 Forbidden)

**Solutions:**
1. This is intentional—printing is restricted to Mon-Fri during school hours
2. To test outside hours: temporarily set DEBUG=True and modify school hour config
3. To disable time restrictions: Remove the `@school_hours_only` decorator in `app.py` (not recommended for production)

## Production Deployment

For production use, follow these recommendations:

1. **Run Behind Reverse Proxy:** Use nginx or Apache to handle HTTPS
2. **Use Systemd Service:** Create a systemd unit file to auto-start the server
3. **Monitor Logs:** Set up log rotation and monitoring
4. **Regular Backups:** Backup the SQLite database daily
5. **Update Passkey:** Rotate the PRINT_PASSKEY regularly
6. **Test Regularly:** Periodically test print jobs to ensure hardware is functioning

### Example Systemd Service File
Create `/etc/systemd/system/pass-printer.service`:

```ini
[Unit]
Description=Mason HS Pass Printer Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pass-printer/print-server
Environment="PATH=/home/pi/pass-printer/print-server/venv/bin"
ExecStart=/home/pi/pass-printer/print-server/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pass-printer
sudo systemctl start pass-printer
```

## Dependencies

- **Flask:** Web framework for HTTP endpoints
- **python-escpos:** ESC/POS protocol for thermal printer communication
- **pytz:** Timezone handling for school hours validation
- **python-dotenv:** Environment variable management

## Contributing

Found a bug or have an improvement? Feel free to open an issue or pull request on GitHub.

## License

See the LICENSE file in the main repository.
