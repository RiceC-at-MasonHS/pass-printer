#!/usr/bin/env bash
# Usage: curl -fsSL https://raw.githubusercontent.com/RiceC-at-MasonHS/pass-printer/main/install.sh | sudo bash
set -euo pipefail

INSTALL_DIR="/opt/pass-printer"
SERVICE_NAME="pass-printer"
REPO_URL="https://github.com/RiceC-at-MasonHS/pass-printer"

# Printer USB IDs — must match app.py
VENDOR_ID="0483"
PRODUCT_ID="5743"

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root: curl ... | sudo bash" >&2
    exit 1
fi

echo "==> Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv libusb-1.0-0 git

echo "==> Fetching repo..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
    git -C "$INSTALL_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo "==> Setting up Python environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/print-server/requirements.txt"

echo "==> Installing udev rule for USB printer..."
cat > /etc/udev/rules.d/99-pass-printer.rules <<EOF
SUBSYSTEM=="usb", ATTRS{idVendor}=="$VENDOR_ID", ATTRS{idProduct}=="$PRODUCT_ID", MODE="0666"
EOF
udevadm control --reload-rules
udevadm trigger

echo "==> Installing systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Mason HS Hall Pass Print Server
After=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/print-server/app.py
WorkingDirectory=${INSTALL_DIR}/print-server
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "==> Done."
echo "    Endpoint : http://$(hostname -I | awk '{print $1}'):5000"
echo "    Status   : systemctl status $SERVICE_NAME"
echo "    Logs     : journalctl -u $SERVICE_NAME -f"
