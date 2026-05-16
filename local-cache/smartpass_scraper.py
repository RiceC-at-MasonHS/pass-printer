import requests
import sqlite3
import time
import os
from datetime import datetime, timedelta
import auth_clever

# --- CONFIGURATION ---
SCHOOL_ID = os.getenv("SMARTPASS_SCHOOL_ID")
SMARTPASS_REGION = os.getenv("SMARTPASS_REGION", "us-central")
API_BASE = f"https://smartpass.app/api/prod-{SMARTPASS_REGION}"
DB_NAME = "/opt/pass-printer/data.db"
MODE = os.getenv("SCRAPER_MODE", "dev") # 'dev' = first 5 students, 'prod' = entire school
RATE_LIMIT_DELAY = 1.0 

def setup_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT, grade TEXT, custom_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedules
                 (student_id INTEGER, period TEXT, start_time TEXT, end_time TEXT, 
                  class_name TEXT, room TEXT, teacher_name TEXT, teacher_email TEXT,
                  FOREIGN KEY(student_id) REFERENCES students(id))''')
    conn.commit()
    return conn

def get_headers(token):
    return {
        "Cookie": f"smartpassToken={token}",
        "x-school-id": SCHOOL_ID,
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

def is_current_semester(course_name):
    """
    Filters courses based on A/B suffix and current date.
    Semester 1: July 1 - Dec 31 (Prefer 'A')
    Semester 2: Jan 1 - June 30 (Prefer 'B')
    """
    month = datetime.now().month
    is_s2 = 1 <= month <= 6 # Jan to June
    
    clean_name = course_name.strip()
    if clean_name.endswith('A'):
        return not is_s2
    if clean_name.endswith('B'):
        return is_s2
    return True # No suffix, assume full year or always current

def sync_data(conn, token):
    headers = get_headers(token)
    
    # 1. Get Students - all at once to minimize auth calls
    print(f"[*] Fetching students (Mode: {MODE})...")
    url = f"{API_BASE}/v1/users?role=_profile_student&include_classes=false&include_activities=false&include_rosters=false"
    student_ids = []
    
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200: 
            print(f"[!] Error fetching students: {resp.status_code}")
            break
        data = resp.json()
        for s in data.get('results', []):
            conn.execute("INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?, ?)", 
                         (s['id'], s['display_name'], s['primary_email'], s['grade_level'], s.get('custom_id')))
            student_ids.append((s['id'], s['display_name']))
            if MODE == 'dev' and len(student_ids) >= 5:
                url = None; break
        conn.commit()

    # 2. Get Agendas
    print(f"[*] Fetching agendas for {len(student_ids)} students...")
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    conn.execute("DELETE FROM schedules")
    
    for sid, name in student_ids:
        print(f"    - {name}...")
        payload = {"user_id": sid, "start_date": today, "end_date": today}
        resp = requests.post(f"{API_BASE}/v2/schedules/GetAgendaForDates", headers=headers, json=payload)
        
        if resp.status_code != 200:
            payload["end_date"] = tomorrow
            resp = requests.post(f"{API_BASE}/v2/schedules/GetAgendaForDates", headers=headers, json=payload)

        if resp.status_code == 200:
            day_data = resp.json().get('days', {}).get(today, {})
            for cls in day_data.get('class_agendas', []):
                c_data = cls.get('class', {})
                c_name = c_data.get('display_name', '')
                
                if not is_current_semester(c_name):
                    continue

                r = c_data.get('room', {})
                t = r.get('teachers', [{}])[0] if r.get('teachers') else {}
                conn.execute("INSERT INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (sid, c_data.get('period_name'), cls.get('start_time'), cls.get('end_time'),
                              c_name, r.get('room'), 
                              t.get('display_name'), t.get('primary_email')))
            conn.commit()
        time.sleep(RATE_LIMIT_DELAY)

if __name__ == "__main__":
    print("[*] Starting Clever Authentication...")
    new_token = auth_clever.get_new_token()
    if not new_token:
        print("[!] Auth failed. Exiting.")
        exit(1)
        
    db_conn = setup_db()
    sync_data(db_conn, new_token)
    db_conn.close()
    print("[+] Sync complete.")
