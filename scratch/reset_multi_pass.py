import sys
import os

# Добавляем родительскую директорию в путь, чтобы найти main и database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _hash_password
from database import SessionLocal, User

def reset_passwords():
    db = SessionLocal()
    try:
        # Получаем всех пользователей с ID от 11 до 14
        users = db.query(User).filter(User.id.in_([11, 12, 13, 14])).all()
        
        if not users:
            print("Пользователи не найдены.")
            return
            
        new_password = "Aa1234@E"
        hashed_password = _hash_password(new_password)
        
        for user in users:
            user.password = hashed_password
            print(f"Пароль для пользователя {user.username} (ID: {user.id}) успешно изменен.")
            
        db.commit()
        print("Все пароли успешно обновлены!")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()
