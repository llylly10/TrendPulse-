import sqlite3
import json
import os
import traceback

DB_NAME = "multi_source.db"
REPORT_FILE = "analysis_report.json"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def test_dashboard():
    try:
        report = {}
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                report = json.load(f)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM cleaned_data")
        total_count = cursor.fetchone()["total"]
        
        cursor.execute("SELECT engagement FROM cleaned_data")
        rows = cursor.fetchall()
        total_engagement = 0
        for row in rows:
            try:
                eng_str = row["engagement"]
                if eng_str:
                    eng = json.loads(eng_str)
                    # Use float() to be safe
                    total_engagement += float(eng.get("score", 0))
                    total_engagement += float(eng.get("view_count", 0))
                    total_engagement += float(eng.get("retweet_count", 0))
                    total_engagement += float(eng.get("like_count", 0))
                    total_engagement += float(eng.get("num_comments", 0))
            except Exception as e:
                print(f"Row error: {e}")
                continue
        
        conn.close()
        heat_index = (total_count * 10) + total_engagement
        print(f"Success! Heat Index: {heat_index}")
        
    except Exception as e:
        print("Global error:")
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard()
