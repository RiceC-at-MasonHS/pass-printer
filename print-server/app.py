"""Flask application for the print server."""

from flask import Flask, jsonify, request

from config import SERVER_HOST, SERVER_PORT, DEBUG
from print_queue import submit_print_job, get_print_job_status, get_print_queue_summary

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "Mason HS Hall Pass Server"}), 200


@app.route("/print", methods=["POST"])
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

