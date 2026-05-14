from flask import Flask, request, jsonify
from escpos.printer import Usb
import datetime

app = Flask(__name__)

# ── Printer ───────────────────────────────────────────────────
VENDOR_ID  = 0x0483
PRODUCT_ID = 0x5743

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

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Mason HS Hall Pass Server"}), 200

@app.route("/print", methods=["POST"])
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
        p.text("MASON HIGH\n")
        p.text("SCHOOL\n")

        p.set(align="center", bold=True, double_height=False, double_width=False)
        p.text("OFFICIAL HALL PASS\n")
        p.text("=" * 42 + "\n")

        # ── Student ─────────────────────────────────────
        p.set(align="left", bold=True, double_height=True, double_width=False)
        p.text(f"{first} {last}\n")

        p.set(align="left", bold=False, double_height=False)
        p.text("-" * 42 + "\n")
        p.text(f"Time Out : {timestamp}\n")
        p.text(f"Reason   : {reason}\n")
        p.text("-" * 42 + "\n")

        # ── Destination ─────────────────────────────────
        p.set(bold=True)
        p.text("DESTINATION\n")
        p.set(bold=False)
        p.text(f"Teacher  : {teacher}\n")

        # ── Footer ──────────────────────────────────────
        p.text("=" * 42 + "\n")
        p.set(align="center")
        p.text("Proceed directly to class.\n")
        p.text("Keep this pass until dismissed.\n\n")

        p.cut()
        p.close()

        return jsonify({"status": "ok", "message": f"Pass printed for {first} {last}"}), 200

    except Exception as e:
        print(f"Print error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

