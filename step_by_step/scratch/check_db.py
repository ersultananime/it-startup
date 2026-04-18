import sqlite3
from pathlib import Path

db_path = Path("data/tracker_v3.db")
if not db_path.exists():
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
