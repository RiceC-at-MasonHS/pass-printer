"""Print queue management and job execution."""

import datetime
import threading
import queue
import time
import uuid
import sqlite3
from escpos.printer import Usb

from config import PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID, PRINT_MAX_RETRIES, SCHOOL_NAME_LINE_1, SCHOOL_NAME_LINE_2, DB_NAME

class PrintJob:
    """Encapsulates a print job with metadata."""
    
    def __init__(self, data):
        self.job_id = str(uuid.uuid4())
        self.data = data
        self.created_at = datetime.datetime.now().isoformat()
        self.attempts = 0
        self.status = "queued"
        self.error_message = None
    
    def to_dict(self):
        """Convert job to dictionary representation."""
        return {
            "job_id": self.job_id,
            "created_at": self.created_at,
            "attempts": self.attempts,
            "status": self.status,
            "error_message": self.error_message,
            "student": f"{self.data.get('first_name', '')} {self.data.get('last_name', '')}",
        }


class PrintQueue:
    """Manages the print queue and background worker."""
    
    def __init__(self):
        self.queue = queue.Queue(maxsize=50) # Limit queue size to prevent overload / attacks
        self.job_status = {}
        self.lock = threading.Lock()
        
        # Start background worker
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def submit_job(self, data):
        """Submit a print job to the queue."""
        job = PrintJob(data)
        self.queue.put(job)
        
        with self.lock:
            self.job_status[job.job_id] = job
        
        return job
    
    def get_job_status(self, job_id):
        """Get status of a specific job."""
        with self.lock:
            return self.job_status.get(job_id)
    
    def get_queue_summary(self):
        """Get overall queue statistics."""
        with self.lock:
            all_jobs = list(self.job_status.values())
        
        return {
            "queued": len([j for j in all_jobs if j.status == "queued"]),
            "processing": len([j for j in all_jobs if j.status == "processing"]),
            "completed": len([j for j in all_jobs if j.status == "completed"]),
            "failed": len([j for j in all_jobs if j.status == "failed"]),
            "recent_jobs": [j.to_dict() for j in all_jobs[-10:]]
        }
    
    def _worker(self):
        """Background worker that processes the print queue."""
        while True:
            try:
                job = self.queue.get(timeout=1)
                self._execute_job(job)
                time.sleep(0.5)  # Small delay between jobs
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Queue worker error: {e}")
    
    def _execute_job(self, job):
        """Execute a print job with retry logic."""
        with self.lock:
            job.status = "processing"
            job.attempts += 1
        
        try:
            printer = self._get_printer()
            if not printer:
                raise Exception("Printer not found/unavailable")
            
            self._print_pass(printer, job)
            
            with self.lock:
                job.status = "completed"
            
            print(f"✓ Printed: {job.data.get('first_name', '')} {job.data.get('last_name', '')} (Job {job.job_id})")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Print error (attempt {job.attempts}/{PRINT_MAX_RETRIES}): {error_msg}")
            
            with self.lock:
                job.error_message = error_msg
                if job.attempts < PRINT_MAX_RETRIES:
                    job.status = "queued"
                    # Re-queue the job
                    self.queue.put(job)
                else:
                    job.status = "failed"
            
            return False
    
    def _get_printer(self):
        """Get USB printer connection."""
        try:
            return Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)
        except Exception as e:
            print(f"Printer connection error: {e}")
            return None
    
    def _print_pass(self, printer, job):
        """Format and print a pass to the thermal printer."""
        first = job.data.get("first_name", "")
        last = job.data.get("last_name", "")
        timestamp = self._format_timestamp(job.data.get("timestamp", ""))
        reason = job.data.get("late_reason", "")
        custom_id = job.data.get("student_id", "")
        
        # Extract schedule data from local-cache (with graceful fallback)
        class_name = "unknown"
        period_number = "unknown"
        room = "unknown"
        teacher_name = "unknown"
        end_time = "unknown"
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT class_name, period_number, room, teacher_name, end_time FROM schedules WHERE student_id = ? LIMIT 1",
                (custom_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                class_name, period_number, room, teacher_name, end_time = result
        except Exception as e:
            print(f"Warning: Could not fetch schedule data for student {custom_id}: {e}")

        # ── Header ──────────────────────────────────────
        printer.set(align="center", bold=True, double_height=True, double_width=True)
        printer.text(f"{SCHOOL_NAME_LINE_1}\n")
        printer.text(f"{SCHOOL_NAME_LINE_2}\n")

        printer.set(align="center", bold=True, double_height=False, double_width=False)
        printer.text("LATE ARRIVAL PASS\n")
        printer.text("=" * 24 + "\n")

        # ── Student ─────────────────────────────────────
        printer.set(align="left", bold=True, double_height=True, double_width=False)
        printer.text(f"{first} {last}\n")

        printer.set(align="left", bold=False, double_height=False)
        printer.text("-" * 47 + "\n")
        printer.text(f"Time In: {timestamp}\n")
        printer.text(f"Reason : {reason}\n")
        printer.text("-" * 47 + "\n")

        # ── Current Class Schedule (from local-cache) ──────
        printer.set(bold=True)
        printer.text("SHOULD BE IN\n")
        printer.set(bold=False)
        printer.text(f"Period : {period_number}\n")
        printer.text(f"Class  : {class_name}\n")
        printer.text(f"Room   : {room}\n")
        printer.text(f"Teacher: {teacher_name}\n")
        if end_time:
            printer.text(f"Until  : {end_time}\n")

        # ── Footer ──────────────────────────────────────
        printer.text("=" * 47 + "\n")
        printer.set(align="center")
        printer.text("Proceed directly to class.\n")
        printer.text("Hand this pass to your teacher.\n\n")

        printer.cut()
        printer.close()
    
    @staticmethod
    def _format_timestamp(ts):
        """Format ISO timestamp to readable format."""
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            local = dt.astimezone()
            return local.strftime("%B %d, %Y  %I:%M %p")
        except:
            return ts


# Global queue instance
_print_queue = PrintQueue()

def submit_print_job(data):
    """Submit a print job to the global queue."""
    return _print_queue.submit_job(data)

def get_print_job_status(job_id):
    """Get status of a print job."""
    return _print_queue.get_job_status(job_id)

def get_print_queue_summary():
    """Get print queue summary."""
    return _print_queue.get_queue_summary()
