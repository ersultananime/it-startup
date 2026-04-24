import sys
import os
import random
from datetime import datetime, timezone, timedelta

# Add parent directory to path so we can import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, User

def main():
    db = SessionLocal()
    try:
        # Fetch users with IDs 11, 12, 13, 14
        users = db.query(User).filter(User.id.in_([11, 12, 13, 14])).all()
        
        if not users:
            print("No users found with IDs 11 to 14.")
            return

        # Time range: April 18, 2026 to April 23, 2026
        start_date = datetime(2026, 4, 18, tzinfo=timezone.utc)
        end_date = datetime(2026, 4, 23, tzinfo=timezone.utc)
        delta = end_date - start_date
        
        for user in users:
            # Generate random time within the range
            random_seconds = random.randint(0, int(delta.total_seconds()))
            new_date = start_date + timedelta(seconds=random_seconds)
            
            user.created_at = new_date
            print(f"Updated user {user.username} (ID: {user.id}) -> {new_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
        db.commit()
        print("Database updated successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
