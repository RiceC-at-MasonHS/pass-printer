#!/bin/bash
# Schedule-Scraper Installer (Side-car for Pass-Printer)
# Installs the Smartpass schedule scraper with proper security (non-root user, systemd services)

set -e

INSTALL_DIR="/opt/schedule-scraper"
PRINTER_DIR="/opt/pass-printer"
SERVICE_USER="schedule-scraper"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[*]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verify running as root
if [ "$EUID" -ne 0 ]; then
   log_error "This installer must be run with sudo"
   exit 1
fi

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
log_info "Found Python $PYTHON_VERSION"

# Create shared printer directory
log_info "Setting up shared database directory..."
mkdir -p $PRINTER_DIR
chmod 755 $PRINTER_DIR

# Create dedicated service user
log_info "Creating dedicated service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d /var/lib/$SERVICE_USER -m $SERVICE_USER
    log_info "Created user: $SERVICE_USER"
else
    log_warn "User $SERVICE_USER already exists"
fi

# Set up installation directory
log_info "Setting up installation directory..."
mkdir -p $INSTALL_DIR

# Check if we need to update ownership/permissions
if [ ! -O $INSTALL_DIR ] || [ "$(stat -c %U $INSTALL_DIR)" != "$SERVICE_USER" ]; then
    chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    log_info "Updated ownership of $INSTALL_DIR"
fi
if [ "$(stat -c %a $INSTALL_DIR)" != "755" ]; then
    chmod 755 $INSTALL_DIR
    log_info "Updated permissions of $INSTALL_DIR"
fi

# Create virtual environment
log_info "Creating Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    sudo -u $SERVICE_USER python3 -m venv $INSTALL_DIR/venv
    log_info "Created new virtual environment"
else
    log_info "Virtual environment already exists"
fi
$INSTALL_DIR/venv/bin/pip install --upgrade pip --quiet

# Install dependencies
log_info "Installing Python dependencies..."
$INSTALL_DIR/venv/bin/pip install -q $(cat requirements.txt | tr '\n' ' ')

# Copy application files
log_info "Installing application files..."
for file in smartpass_scraper.py auth_clever.py main.py SCHEMA.md README.md; do
    if [ ! -f "$INSTALL_DIR/$file" ]; then
        cp $file $INSTALL_DIR/
        log_info "Installed: $file"
    else
        log_info "Already exists: $file (skipping)"
    fi
done

chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/*.py $INSTALL_DIR/*.md 2>/dev/null || true
chmod 644 $INSTALL_DIR/*.py $INSTALL_DIR/*.md 2>/dev/null || true

# Create .env from example if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    log_warn "Configuration file missing!"
    log_info "Copying .env.example to .env"
    cp .env.example $INSTALL_DIR/.env
    chmod 600 $INSTALL_DIR/.env
    chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env
    log_warn "IMPORTANT: Edit $INSTALL_DIR/.env with your Clever credentials before starting services"
else
    log_info "Configuration file already exists at $INSTALL_DIR/.env"
fi

# Check if configuration is complete
if grep -q "your_" $INSTALL_DIR/.env; then
    log_warn "⚠️  Configuration incomplete - .env still contains placeholder values"
    log_warn "Edit: $INSTALL_DIR/.env"
fi

# Create systemd service for daily sync
log_info "Installing systemd service (daily sync at 3 AM)..."
tee /etc/systemd/system/schedule-scraper.service > /dev/null <<EOF
[Unit]
Description=Smartpass Schedule Scraper Daily Sync
After=network.target
Documentation=$INSTALL_DIR/README.md

[Service]
Type=oneshot
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python smartpass_scraper.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer for daily sync
log_info "Installing systemd timer..."
tee /etc/systemd/system/schedule-scraper.timer > /dev/null <<EOF
[Unit]
Description=Run Smartpass Scraper Daily at 3 AM
Documentation=$INSTALL_DIR/README.md

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Create systemd service for web API
log_info "Installing systemd service (local API on port 48273)..."
tee /etc/systemd/system/schedule-scraper-api.service > /dev/null <<EOF
[Unit]
Description=Smartpass Schedule Scraper API Server
After=network.target
Documentation=$INSTALL_DIR/README.md

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 48273
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set up database directory (shared with print-server)
log_info "Configuring database directory..."
if [ ! -d "$PRINTER_DIR" ]; then
    mkdir -p $PRINTER_DIR
    log_info "Created $PRINTER_DIR"
else
    log_warn "Database directory already exists (preserving existing data)"
fi

# Ensure correct permissions without overwriting data
if [ -d "$PRINTER_DIR" ]; then
    if [ "$(stat -c %U $PRINTER_DIR)" != "$SERVICE_USER" ] || [ "$(stat -L -c %g $PRINTER_DIR)" != "$SERVICE_USER" ]; then
        log_info "Updating ownership of $PRINTER_DIR"
        chown $SERVICE_USER:$SERVICE_USER $PRINTER_DIR
    fi
    if [ "$(stat -c %a $PRINTER_DIR)" != "755" ]; then
        log_info "Updating permissions of $PRINTER_DIR"
        chmod 755 $PRINTER_DIR
    fi
fi

# Reload systemd and enable services
log_info "Configuring systemd services..."
systemctl daemon-reload

# Enable services (safe to run multiple times)
systemctl enable schedule-scraper.timer 2>/dev/null || log_warn "Timer already enabled"
systemctl enable schedule-scraper-api.service 2>/dev/null || log_warn "API service already enabled"

# Check if we need to start services
if ! systemctl is-active --quiet schedule-scraper-api.service; then
    log_info "Starting API service..."
    systemctl start schedule-scraper-api.service
else
    log_warn "API service already running (run 'sudo systemctl restart schedule-scraper-api' to restart)"
fi

if ! systemctl is-active --quiet schedule-scraper.timer; then
    log_info "Activating daily sync timer..."
    systemctl start schedule-scraper.timer
else
    log_warn "Sync timer already active"
fi

echo ""
echo -e "${GREEN}[+] Installation complete!${NC}"
echo ""
echo "Service User: $SERVICE_USER"
echo "Install Directory: $INSTALL_DIR"
echo "Database Location: $PRINTER_DIR/data.db"
echo "Config File: $INSTALL_DIR/.env"
echo ""
echo "Systemd Services:"
echo "  - schedule-scraper.timer       (Daily sync at 3:00 AM)"
echo "  - schedule-scraper.service     (Manual sync via: sudo systemctl start schedule-scraper)"
echo "  - schedule-scraper-api.service (Local API on http://127.0.0.1:48273)"
echo ""
echo "Status Commands:"
echo "  sudo systemctl status schedule-scraper-api.service"
echo "  sudo systemctl status schedule-scraper.timer"
echo ""
echo "Logs:"
echo "  sudo journalctl -u schedule-scraper-api -f"
echo "  sudo journalctl -u schedule-scraper -f"
echo ""
echo "Manual Sync:"
echo "  curl -X POST http://127.0.0.1:48273/sync"
echo "  curl http://127.0.0.1:48273/stats"
echo ""
