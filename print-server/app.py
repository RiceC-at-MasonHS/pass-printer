"""Flask application for the print server."""

from flask import Flask, jsonify, request
import datetime
import pytz
from functools import wraps

from config import SERVER_HOST, SERVER_PORT, DEBUG, SERVICE_NAME, TIMEZONE, SCHOOL_START_HOUR, SCHOOL_START_MINUTE, SCHOOL_END_HOUR, SCHOOL_END_MINUTE
from print_queue import submit_print_job, get_print_job_status, get_print_queue_summary

app = Flask(__name__)

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
    """Submit a print job to the queue."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    # Submit job to queue
    job = submit_print_job(data)
    
    print(f"→ Queued: {data.get('first_name', '')} {data.get('last_name', '')} (Job {job.job_id})")
    
    return jsonify({
        "status": "queued",
        "job_id": job.job_id,
        "message": f"Pass queued for printing. Check status with /status/{job.job_id}"
    }), 202


@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id):
    """Check the status of a print job."""
    job = get_print_job_status(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(job.to_dict()), 200


@app.route("/queue", methods=["GET"])
def get_queue_status():
    """Get overall queue status and job summary."""
    summary = get_print_queue_summary()
    return jsonify(summary), 200


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG)

