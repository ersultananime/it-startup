import sqlite3
import os

def update_database():
    # Database path
    db_path = os.path.join("data", "tracker_v3.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Connecting to database: {db_path}...")

        # Add is_paid column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_paid BOOLEAN DEFAULT FALSE;")
            print("Column 'is_paid' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'is_paid' already exists.")
            else:
                raise e

        # Add payment_ref column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN payment_ref TEXT;")
            print("Column 'payment_ref' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'payment_ref' already exists.")
            else:
                raise e

        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Database update completed.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_database()
