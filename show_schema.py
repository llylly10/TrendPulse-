import sqlite3, os, sys

db_path = os.path.join(os.path.dirname(__file__), 'multi_source.db')
if not os.path.exists(db_path):
    print('Database not found at', db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
rows = cur.fetchall()
for row in rows:
    if row[0]:
        print(row[0])
conn.close()
