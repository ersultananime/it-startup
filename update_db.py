import sqlite3
import os

def update_database():
    db_path = os.path.join("data", "tracker_v3.db")
    
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns = [
        ("goal_label", "TEXT DEFAULT ''"),
        ("is_premium", "BOOLEAN DEFAULT 0"),
        ("is_paid", "BOOLEAN DEFAULT 0"),
        ("payment_ref", "TEXT")
    ]

    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
            print(f"Column '{col_name}' added.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column '{col_name}' already exists.")
            else:
                print(f"Error adding '{col_name}': {e}")

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    update_database()
