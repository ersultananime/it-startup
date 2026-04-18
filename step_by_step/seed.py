"""
seed.py - Script to populate the database with initial users, goals, and activity logs.
"""
from passlib.context import CryptContext
from app.database import Base, engine, SessionLocal
from app.models import User, Goal, ActivityLog
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Create a dummy user
        print("Checking for existing users...")
        user = db.query(User).filter(User.name == "DemoUser").first()
        if not user:
            print("Creating DemoUser...")
            hashed_password = pwd_context.hash("demo1234")
            user = User(
                name="DemoUser",
                password=hashed_password,
                weight_kg=78.5,
                height_cm=180.0,
                activity_level="medium"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            print("DemoUser already exists.")
            
        # 2. Create goals for this user
        print("Checking goals...")
        goal = db.query(Goal).filter(Goal.user_id == user.id).first()
        if not goal:
            print("Creating goals for DemoUser...")
            goal = Goal(
                user_id=user.id,
                title="Пройти 100 000 шагов за месяц",
                target_value=100000.0,
                daily_target=3500.0,
                unit="steps"
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)
            
            # 3. Create activity logs
            print("Creating activity logs...")
            log1 = ActivityLog(
                user_id=user.id,
                goal_id=goal.id,
                value=3600.0,
                unit="steps",
                daily_pct=100.0,
                global_pct=3.6
            )
            log2 = ActivityLog(
                user_id=user.id,
                goal_id=goal.id,
                value=1500.0,
                unit="steps",
                daily_pct=42.8,
                global_pct=5.1
            )
            db.add_all([log1, log2])
            db.commit()
        else:
            print("Goals already exist.")
            
        print("Database seeded successfully!")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
