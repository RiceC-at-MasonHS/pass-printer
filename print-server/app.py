from flask import Flask, request, jsonify
from escpos.printer import Usb
import datetime
from functools import wraps
import pytz
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Configuration ─────────────────────────────────────────────
SCHOOL_NAME_LINE_1 = os.getenv("SCHOOL_NAME_LINE_1", "MASON HIGH")
SCHOOL_NAME_LINE_2 = os.getenv("SCHOOL_NAME_LINE_2", "SCHOOL")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Mason HS Hall Pass Server")
TIMEZONE = os.getenv("TIMEZONE", "US/Eastern")
SCHOOL_START_HOUR = int(os.getenv("SCHOOL_START_HOUR", "7"))
SCHOOL_START_MINUTE = int(os.getenv("SCHOOL_START_MINUTE", "30"))
SCHOOL_END_HOUR = int(os.getenv("SCHOOL_END_HOUR", "14"))
SCHOOL_END_MINUTE = int(os.getenv("SCHOOL_END_MINUTE", "30"))

# ── Printer ───────────────────────────────────────────────────
VENDOR_ID  = int(os.getenv("PRINTER_VENDOR_ID", "0x0483"), 16)
PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID", "0x5743"), 16)

def get_printer():
    try:
        return Usb(VENDOR_ID, PRODUCT_ID)
    except Exception as e:
        print(f"Printer connection error: {e}")
        return None

def format_timestamp(ts):
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        local = dt.astimezone()
        return local.strftime("%B %d, %Y  %I:%M %p")
    except:
        return ts

def school_hours_only(f):
    """
    Decorator that restricts endpoint access to school hours:
    - Monday through Friday only
    - Time range configured via environment variables (default: 7:30 AM to 2:30 PM)
    - Timezone configured via environment variables (default: US/Eastern)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get current time in configured timezone
        tz = pytz.timezone(TIMEZONE)
        now = datetime.datetime.now(tz)
        
        # Check if it's a weekday (0=Monday, 4=Friday, 5=Saturday, 6=Sunday)
        if now.weekday() >= 5:
            return jsonify({
                "error": "Printing disabled on weekends",
                "current_time": now.strftime("%A %I:%M %p %Z")
            }), 403
        
        # Check if time is within configured school hours
        school_start = now.replace(hour=SCHOOL_START_HOUR, minute=SCHOOL_START_MINUTE, second=0, microsecond=0)
        school_end = now.replace(hour=SCHOOL_END_HOUR, minute=SCHOOL_END_MINUTE, second=0, microsecond=0)
        
        if now < school_start or now > school_end:
            start_str = f"{SCHOOL_START_HOUR}:{SCHOOL_START_MINUTE:02d} AM"
            end_str = f"{SCHOOL_END_HOUR if SCHOOL_END_HOUR <= 12 else SCHOOL_END_HOUR - 12}:{SCHOOL_END_MINUTE:02d} PM"
            return jsonify({
                "error": f"Printing only allowed between {start_str} and {end_str} {TIMEZONE}",
                "current_time": now.strftime("%A %I:%M %p %Z")
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def health():
    return jsonify({"status": "ok", "service": SERVICE_NAME}), 200

@app.route("/print", methods=["POST"])
@school_hours_only
def print_pass():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    p = get_printer()
    if not p:
        return jsonify({"error": "Printer not found"}), 500

    try:
        first     = data.get("first_name", "")
        last      = data.get("last_name", "")
        timestamp = format_timestamp(data.get("timestamp", ""))
        reason    = data.get("late_reason", "")
        dest      = data.get("heading_to", {})
        teacher   = dest.get("teacher", "")

        # ── Header ──────────────────────────────────────
        p.set(align="center", bold=True, double_height=True, double_width=True)
        p.text(f"{SCHOOL_NAME_LINE_1}\n")
        p.text(f"{SCHOOL_NAME_LINE_2}\n")

        p.set(align="center", bold=True, double_height=False, double_width=False)
        p.text("OFFICIAL HALL PASS\n")
        p.text("=" * 24 + "\n")

        # ── Student ─────────────────────────────────────
        p.set(align="left", bold=True, double_height=True, double_width=False)
        p.text(f"{first} {last}\n")

        p.set(align="left", bold=False, double_height=False)
        p.text("-" * 47 + "\n")
        p.text(f"Sign In  : {timestamp}\n")
        p.text(f"Reason   : {reason}\n")
        p.text("-" * 47 + "\n")

        # ── Destination ─────────────────────────────────
        p.set(bold=True)
        p.text("DESTINATION\n")
        p.set(bold=False)
        p.text(f"Teacher  : {teacher}\n")

        # ── Footer ──────────────────────────────────────
        p.text("=" * 47 + "\n")
        p.set(align="center")
        p.text("Proceed directly to class.\n")
        p.text("Hand this pass to the teacher.")

        p.cut()
        p.close()

        return jsonify({"status": "ok", "message": f"Pass printed for {first} {last}"}), 200

    except Exception as e:
        print(f"Print error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "5000"))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(host=host, port=port, debug=debug)

