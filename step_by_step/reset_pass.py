from main import pwd_context
from database import SessionLocal, User

def reset_password(username, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"User '{username}' not found.")
            return
        
        # Хешируем новый пароль текущим алгоритмом
        user.password = pwd_context.hash(new_password)
        db.commit()
        print(f"Password for user '{username}' has been reset successfully to: {new_password}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Вы можете изменить имя пользователя или пароль ниже
    reset_password("Ерсултан", "12345678")
