import sys
import os

# Добавляем родительскую директорию в путь, чтобы найти main и database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _verify_password
from database import SessionLocal, User

db = SessionLocal()
user = db.query(User).filter(User.username == "Aris").first()
if not user:
    print("User Aris not found.")
else:
    print(f"User found: ID={user.id}, Username='{user.username}'")
    print("Stored hash:", user.password)
    match = _verify_password("Aa1234@E", user.password)
    print("Match with Aa1234@E:", match)
db.close()
