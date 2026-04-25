import sqlite3

ids_to_delete = [1, 3, 4]

try:
    conn = sqlite3.connect("data/tracker_v3.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username LIKE '%test%' OR username LIKE '%http%'")
    conn.commit()
    print(f"Удалено строк: {cur.rowcount}")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    conn.close()
