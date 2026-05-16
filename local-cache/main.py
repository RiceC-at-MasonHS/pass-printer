from fastapi import FastAPI, BackgroundTasks
import smartpass_scraper
import os
import sqlite3

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Smartpass Scraper API Ready"}

@app.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks):
    # Fresh DB for the day
    if os.path.exists(smartpass_scraper.DB_NAME):
        os.remove(smartpass_scraper.DB_NAME)
    
    def run_sync():
        db_conn = smartpass_scraper.setup_db()
        smartpass_scraper.get_students(db_conn)
        smartpass_scraper.get_agendas(db_conn)
        smartpass_scraper.export_csv(db_conn)
        db_conn.close()
        print("[+] Background sync complete.")

    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background"}

@app.get("/stats")
def get_stats():
    if not os.path.exists(smartpass_scraper.DB_NAME):
        return {"error": "No data yet. Run /sync first."}
    
    conn = sqlite3.connect(smartpass_scraper.DB_NAME)
    student_count = conn.execute("SELECT count(*) FROM students").fetchone()[0]
    schedule_count = conn.execute("SELECT count(*) FROM schedules").fetchone()[0]
    conn.close()
    
    return {
        "students_synced": student_count,
        "schedule_rows": schedule_count
    }
