#!/usr/bin/env bash
# Pass-Printer Main Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/RiceC-at-MasonHS/pass-printer/main/install.sh | sudo bash

set -euo pipefail

INSTALL_DIR="/opt/pass-printer"
REPO_URL="https://github.com/RiceC-at-MasonHS/pass-printer"
SERVICE_NAME="pass-printer"
SERVICE_USER="pass-printer"

# Printer USB IDs — must match your printer hardware
VENDOR_ID="0483"
PRODUCT_ID="5743"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_section() {
    echo ""
    echo -e "${BLUE}==> $1${NC}"
}

# Verify running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This installer must be run as root"
    echo "Try: curl -fsSL https://raw.githubusercontent.com/RiceC-at-MasonHS/pass-printer/main/install.sh | sudo bash"
    exit 1
fi

log_section "Installing system dependencies..."
log_info "Updating package manager..."
apt-get update -qq

log_info "Installing required packages..."
REQUIRED_PACKAGES="python3 python3-pip python3-venv libusb-1.0-0 git"
apt-get install -y -qq $REQUIRED_PACKAGES

log_section "Setting up repository..."

if [[ -d "$INSTALL_DIR/.git" ]]; then
    log_warn "Repository already exists, pulling latest changes..."
    if git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null; then
        log_info "Repository updated"
    else
        log_warn "Could not fast-forward pull; repository may have local changes"
    fi
else
    log_info "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Verify repository structure
if [[ ! -d "$INSTALL_DIR/print-server" ]]; then
    log_error "Repository structure invalid: print-server directory not found"
    log_error "Expected: $INSTALL_DIR/print-server"
    log_error "Please verify the repository was cloned correctly"
    exit 1
fi

if [[ ! -f "$INSTALL_DIR/print-server/requirements.txt" ]]; then
    log_error "Missing requirements.txt: $INSTALL_DIR/print-server/requirements.txt"
    log_error "Repository may be incomplete or corrupted"
    exit 1
fi

log_info "Repository structure verified"

log_section "Setting up service user..."

if id "$SERVICE_USER" &>/dev/null; then
    log_warn "Service user '$SERVICE_USER' already exists"
else
    log_info "Creating dedicated service user..."
    useradd -r -s /bin/bash -d /var/lib/$SERVICE_USER -m $SERVICE_USER
fi

log_section "Creating shared database directory..."

if [[ ! -d "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR"
    log_info "Created $INSTALL_DIR"
fi

# Ensure proper ownership (but don't destroy existing data)
if [[ -O "$INSTALL_DIR" && "$(stat -c %U $INSTALL_DIR)" == "$SERVICE_USER" ]]; then
    log_info "Directory ownership already correct"
else
    log_info "Updating directory ownership to $SERVICE_USER"
    chown $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
fi

log_section "Setting up Python environment..."

VENV_PATH="$INSTALL_DIR/venv"

if [[ ! -d "$VENV_PATH" ]]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
else
    log_info "Virtual environment already exists"
fi

log_info "Installing/updating pip..."
"$VENV_PATH/bin/pip" install --quiet --upgrade pip 2>/dev/null || log_warn "pip already up-to-date"

log_info "Installing Python dependencies..."
"$VENV_PATH/bin/pip" install --quiet -r "$INSTALL_DIR/print-server/requirements.txt"

log_section "Configuring USB printer access..."

UDEV_RULE_FILE="/etc/udev/rules.d/99-pass-printer.rules"
NEW_RULE="SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"$VENDOR_ID\", ATTRS{idProduct}==\"$PRODUCT_ID\", MODE=\"0666\""

if [[ -f "$UDEV_RULE_FILE" ]]; then
    if grep -q "VENDOR.*$VENDOR_ID" "$UDEV_RULE_FILE"; then
        log_info "udev rule already exists"
    else
        log_warn "udev rule file exists but may not match current printer IDs"
        log_info "Updating udev rule..."
        echo "$NEW_RULE" > "$UDEV_RULE_FILE"
        udevadm control --reload-rules
        udevadm trigger
    fi
else
    log_info "Creating udev rule for USB printer..."
    echo "$NEW_RULE" > "$UDEV_RULE_FILE"
    udevadm control --reload-rules
    udevadm trigger
fi

log_section "Configuring systemd service..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Create the service file
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Mason HS Hall Pass Print Server
After=network.target
Documentation=$INSTALL_DIR/print-server/README.md

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/print-server
EnvironmentFile=$INSTALL_DIR/print-server/.env
ExecStart=$VENV_PATH/bin/python app.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

log_info "Service file configured"

# Setup .env if missing
if [[ ! -f "$INSTALL_DIR/print-server/.env" ]]; then
    log_warn "No .env configuration found!"
    if [[ -f "$INSTALL_DIR/print-server/.env.example" ]]; then
        log_info "Copying .env.example to .env"
        cp "$INSTALL_DIR/print-server/.env.example" "$INSTALL_DIR/print-server/.env"
        chmod 600 "$INSTALL_DIR/print-server/.env"
        chown $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR/print-server/.env"
        log_warn "Please edit: $INSTALL_DIR/print-server/.env with your configuration"
    else
        log_error "Could not find .env.example template"
    fi
else
    log_info ".env configuration already exists"
fi

log_section "Enabling systemd service..."

systemctl daemon-reload

if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
    log_info "Service already enabled"
else
    log_info "Enabling service to start on boot..."
    systemctl enable "$SERVICE_NAME"
fi

# Check if service is already running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_info "Service is running, restarting to load latest code..."
    systemctl restart "$SERVICE_NAME"
else
    log_info "Starting service..."
    systemctl start "$SERVICE_NAME"
fi

log_section "Installation Complete"

echo ""
echo -e "${GREEN}✓ Pass-Printer is installed and running!${NC}"
echo ""
echo "Service User:      $SERVICE_USER"
echo "Install Directory: $INSTALL_DIR"
echo "Database Location: $INSTALL_DIR/data.db"
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "  Status:  systemctl status $SERVICE_NAME"
echo "  Logs:    journalctl -u $SERVICE_NAME -f"
echo "  Restart: systemctl restart $SERVICE_NAME"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Configure the print server: edit $INSTALL_DIR/print-server/.env"
echo "  2. Find your printer USB IDs:  lsusb"
echo "  3. Update PRINTER_VENDOR_ID and PRINTER_PRODUCT_ID if needed"
echo "  4. Install the schedule-scraper: cd $INSTALL_DIR/local-cache && sudo ./install.sh"
echo "  5. Configure Google Apps Script and Forms"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  Print Server:  $INSTALL_DIR/print-server/README.md"
echo "  Local Cache:   $INSTALL_DIR/local-cache/README.md"
echo "  Main README:   $INSTALL_DIR/README.md"
echo ""
