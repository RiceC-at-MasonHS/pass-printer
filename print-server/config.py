"""Configuration module for print server."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Printer Configuration ──────────────────────────────────────
PRINTER_VENDOR_ID = int(os.getenv("PRINTER_VENDOR_ID", "0x0483"), 16)
PRINTER_PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID", "0x5743"), 16)

# ── Print Queue Configuration ──────────────────────────────────
PRINT_MAX_RETRIES = int(os.getenv("PRINT_MAX_RETRIES", "5"))
PRINT_RETRY_DELAY = int(os.getenv("PRINT_RETRY_DELAY", "5"))  # seconds

# ── Security Configuration ──────────────────────────────────
PRINT_PASSKEY = os.getenv("PRINT_PASSKEY", "")

# ── Server Configuration ───────────────────────────────────────
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
