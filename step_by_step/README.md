# Step by Step 🏃

> Платформа мягкого фитнеса — без осуждения, без стресса.  
> Цели в **действиях**, прогресс-бары и алгоритм «Мягкого возврата».

---

## Структура проекта

```
step_by_step/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # SQLAlchemy + SQLite
│   ├── models.py            # ORM: users, goals, activity_log
│   ├── schemas.py           # Pydantic v2 schemas
│   ├── progress.py          # Progress Engine + ASCII progress bar
│   ├── soft_return.py       # Алгоритм «Мягкого возврата»
│   ├── motivations.py       # Мотивационные сообщения
│   └── routers/
│       ├── users.py         # POST /users, GET /users/{id}
│       ├── goals.py         # POST /goals, GET /goals/{id}
│       └── activity.py      # POST /log-activity  ← ключевой эндпоинт
└── tests/
    ├── test_progress.py
    ├── test_motivations.py
    └── test_api.py
```

---

## Быстрый старт

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Запустить тесты

```bash
pytest tests/ -v
```

---

## Ключевые эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/users/` | Создать профиль |
| `GET`  | `/users/{id}` | Получить профиль |
| `POST` | `/goals/` | Создать цель (в действиях!) |
| `POST` | `/log-activity` | Записать тренировку → прогресс + мотивация |

---

## POST /log-activity — Пример

**Запрос:**
```json
{
  "user_id": 1,
  "goal_id": 1,
  "value": 1500,
  "unit": "steps"
}
```

**Ответ:**
```json
{
  "log_id": 3,
  "daily_pct": 50.0,
  "global_pct": 5.0,
  "progress_bar": "[█████░░░░░] 50%",
  "motivation": "💪 Отличный старт! Ты уже набираешь ритм...",
  "soft_return": null
}
```

**Если пользователь не тренировался 3+ дня:**
```json
{
  "soft_return": {
    "days_missed": 5,
    "suggested_daily_target": 1500.0,
    "unit": "steps",
    "message": "Ты отсутствовал(а) 5 дн. — это нормально... 🤗"
  }
}
```

---

## Алгоритм «Мягкого возврата»

| Условие | Действие |
|---------|----------|
| 0–2 пропущенных дня | Всё нормально, стандартная цель |
| 3+ пропущенных дня | `daily_target × 0.5` + мотивирующее сообщение |

> Система никогда не ругает пользователя — только предлагает «шаг назад».

---

## Прогресс-бар

```
[░░░░░░░░░░]  0%  ← старт
[██░░░░░░░░] 20%  ← первые шаги  
[█████░░░░░] 50%  ← половина
[██████████] 100% ← цель дня!
```

Заполняется даже от минимального вклада.
