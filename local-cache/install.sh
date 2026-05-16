#!/bin/bash
# Schedule-Scraper Installer (Side-car for Pass-Printer)

INSTALL_DIR="/opt/schedule-scraper"
PRINTER_DIR="/opt/pass-printer"
USER=$(whoami)

echo "[*] Setting up directory..."
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

echo "[*] Creating virtual environment..."
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate
pip install fastapi uvicorn requests playwright --quiet
playwright install-deps chromium
playwright install chromium

echo "[*] Copying files..."
cp smartpass_scraper.py auth_clever.py main.py requirements.txt SCHEMA.md README.md $INSTALL_DIR/

echo "[*] Creating systemd service (Daily Sync)..."
sudo tee /etc/systemd/system/schedule-scraper.service <<EOF
[Unit]
Description=Smartpass Schedule Scraper
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/smartpass_scraper.py
EOF

echo "[*] Creating systemd timer (Daily 3 AM)..."
sudo tee /etc/systemd/system/schedule-scraper.timer <<EOF
[Unit]
Description=Run Smartpass Scraper Daily

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "[*] Creating systemd service for Web API (Port 48273)..."
sudo tee /etc/systemd/system/schedule-scraper-api.service <<EOF
[Unit]
Description=Smartpass Schedule Scraper API
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 48273
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable schedule-scraper.timer
sudo systemctl enable schedule-scraper-api.service
sudo systemctl start schedule-scraper-api.service

echo "[+] Installation complete."
echo "Config lives in $INSTALL_DIR/.env"
echo "Database shared at $PRINTER_DIR/data.db"
echo "Local API reachable at http://127.0.0.1:48273"
