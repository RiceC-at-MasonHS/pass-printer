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

# ── School Configuration ─────────────────────────────────────────────
SCHOOL_NAME_LINE_1 = os.getenv("SCHOOL_NAME_LINE_1", "MASON HIGH")
SCHOOL_NAME_LINE_2 = os.getenv("SCHOOL_NAME_LINE_2", "SCHOOL")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Mason HS Hall Pass Server")
TIMEZONE = os.getenv("TIMEZONE", "US/Eastern")
SCHOOL_START_HOUR = int(os.getenv("SCHOOL_START_HOUR", "7"))
SCHOOL_START_MINUTE = int(os.getenv("SCHOOL_START_MINUTE", "30"))
SCHOOL_END_HOUR = int(os.getenv("SCHOOL_END_HOUR", "14"))
SCHOOL_END_MINUTE = int(os.getenv("SCHOOL_END_MINUTE", "30"))