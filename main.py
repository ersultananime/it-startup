"""
main.py — Step by Step MVP Web Application
Run: uvicorn main:app --reload
Open: http://127.0.0.1:8000
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import os
import random

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, User, WorkoutLog, engine, get_db
import openai
from openai import OpenAI
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()
try:
    api_key = os.environ.get("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=api_key)
except Exception:
    openai_client = None

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)



# ── Progress Engine ───────────────────────────────────────────────────────────
def calculate_progress(start: float, current: float, target: float) -> float:
    """Return overall completion percentage based on weight loss/gain."""
    if start == target:
        return 100.0
    
    # Calculate progress. If moving away from target, it goes negative, we clamp to 0-100.
    total_to_lose = abs(start - target)
    amount_lost = abs(start - current)
    
    # Make sure we're actually progressing in the right direction
    if (start > target and current > start) or (start < target and current < start):
        return 0.0
        
    pct = (amount_lost / total_to_lose) * 100
    return min(max(round(pct, 1), 0.0), 100.0)


def calculate_bmi(weight: float, height_cm: float) -> float:
    """Calculate Body Mass Index."""
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight / (height_m * height_m), 1)


def get_motivation(pct: float) -> str:
    if pct >= 100:
        return "🏆 Цель достигнута! Потрясающий результат!"
    if pct >= 80:
        return "🔥 Финишная прямая! Ты в отличной форме!"
    if pct >= 50:
        return "💪 Половина пути пройдена. Так держать!"
    if pct >= 20:
        return "🌱 Процесс пошел! Первые результаты уже есть."
    if pct > 0:
        return "🌱 Начало положено! Продолжай в том же духе."
    return "🚀 Путь в 1000 ли начинается с первого шага!"


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="Step by Step")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Get the logged-in user from the session cookie."""
    user_id = request.cookies.get("session_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()


def _get_active_user(db: Session) -> Optional[User]:
    """Fallback for old logic - not recommended for multi-user."""
    return db.query(User).order_by(User.id.asc()).first()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard. Shows auth modal if not logged in."""
    user = get_current_user(request, db)
    
    if not user:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "user": None,
            "pct": 0,
            "bmi": 0,
            "is_premium": False,
            "motivation": "",
            "logs": []
        })

    pct = calculate_progress(user.start_weight_kg, user.current_weight_kg, user.target_weight_kg)
    bmi = calculate_bmi(user.current_weight_kg, user.height_cm)
    
    logs = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user.id)
        .order_by(WorkoutLog.date.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "pct": pct,
            "bmi": bmi,
            "is_premium": user.is_premium,
            "motivation": get_motivation(pct),
            "logs": logs,
        },
    )


@app.post("/api/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    height_cm: float = Form(...),
    current_weight_kg: float = Form(...),
    target_weight_kg: float = Form(...),
    goal_label: str = Form(...),
    payment_digits: str = Form(...),
    db: Session = Depends(get_db),
):
    """Register a new user and set session cookie."""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return JSONResponse({"error": "Username already taken"}, status_code=400)
    
    user = User(
        username=username,
        password=pwd_context.hash(password),
        name=name,
        height_cm=height_cm,
        start_weight_kg=current_weight_kg,
        current_weight_kg=current_weight_kg,
        target_weight_kg=target_weight_kg,
        goal_label=goal_label,
        payment_ref=payment_digits,
        is_paid=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    response = JSONResponse({"success": True})
    response.set_cookie(key="session_id", value=str(user.id), httponly=True)
    return response


@app.post("/api/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Login and set session cookie."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password):
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)
    
    response = JSONResponse({"success": True})
    response.set_cookie(key="session_id", value=str(user.id), httponly=True)
    return response


@app.post("/api/logout")
def logout():
    """Clear session cookie."""
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session_id")
    return response


@app.post("/api/checkout")
def checkout(request: Request, db: Session = Depends(get_db)):
    """Simulate payment and grant Premium status."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Auth required"}, status_code=401)
    
    user.is_premium = True
    db.commit()
    return JSONResponse({"success": True})


class PaymentRequest(BaseModel):
    card_number: str
    expiry: str
    cvv: str
    cardholder: str

@app.post("/process-payment")
def process_payment(payment: PaymentRequest):
    """Process card payment for registration."""
    card = payment.card_number.replace(" ", "").replace("-", "")
    if len(card) == 16 and card.isdigit():
        return {"success": True}
    return JSONResponse({"success": False, "error": "Неверный номер карты. Ожидается 16 цифр."}, status_code=400)


@app.post("/api/ai_chat")
def ai_chat(request: Request, message: str = Form(...), db: Session = Depends(get_db)):
    """AI Trainer chat session for Premium users."""
    user = get_current_user(request, db)
    if not user or not user.is_premium:
        return JSONResponse({"error": "Premium required"}, status_code=403)
    
    bmi = calculate_bmi(user.current_weight_kg, user.height_cm)
    
    dummy_keys = ["your-api-key-here", "sk-your-api-key-here", ""]
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    
    if not openai_client or not api_key or api_key in dummy_keys:
        msg_lower = message.lower()
        if "пит" in msg_lower or "еда" in msg_lower or "диет" in msg_lower or "сахар" in msg_lower:
            category = "nutrition"
        elif "сон" in msg_lower or "спат" in msg_lower or "восстановл" in msg_lower:
            category = "sleep"
        elif "лен" in msg_lower or "мотивац" in msg_lower or "устал" in msg_lower or "психолог" in msg_lower:
            category = "psychology"
        elif "актив" in msg_lower or "шаг" in msg_lower or "ход" in msg_lower or "быт" in msg_lower:
            category = "activity"
        else:
            category = random.choice(["nutrition", "sleep", "psychology", "activity"])

        if category == "nutrition":
            mock_resp = random.choice([
                "Простая привычка: выпивай стакан воды за 15 минут до еды. Это улучшает пищеварение и спасает от переедания.\n\nКакую полезную еду ты любишь больше всего?",
                "Попробуй заменить привычные сладости на фрукты или орехи. Маленькие изменения дают большой результат!\n\nКакой твой любимый полезный перекус?",
                "Главное правило здоровой тарелки — больше ярких овощей. Они дают сытость и минимум калорий.\n\nЧто сегодня было у тебя на завтрак?"
            ])
        elif category == "sleep":
            mock_resp = random.choice([
                "Сон — твой главный помощник в здоровье. Старайся спать 7-8 часов, это нормализует уровень стресса.\n\nВо сколько ты обычно ложишься спать?",
                "Во время глубокого сна восстанавливается весь организм. Хороший отдых буквально делает нас здоровее!\n\nКак ты сегодня спал?",
                "За час до сна лучше убрать гаджеты. Синий свет мешает выработке мелатонина.\n\nУдается ли тебе отдыхать вечером перед сном?"
            ])
        elif category == "psychology":
            mock_resp = random.choice([
                "Лень — это абсолютно нормально! Не нужно ругать себя. Просто сделай самую малость, например, 5 минут растяжки.\n\nЗа что ты сегодня можешь себя похвалить?",
                "Путь к приятным изменениям состоит из маленьких шагов. Отмечай каждую крошечную победу.\n\nКакое маленькое достижение сегодня тебя порадовало?",
                "Не страшно пропустить занятие. Тревога из-за пропусков вредит больше, чем сам пропуск.\n\nКак твое настроение сегодня в целом?"
            ])
        else:
            mock_resp = random.choice([
                "Сжигать калории можно незаметно: выбирай лестницу вместо лифта или гуляй во время долгих звонков.\n\nКакая у тебя любимая повседневная активность?",
                "Даже 15 минут легкой прогулки на свежем воздухе лучше, чем ничего. Движение должно приносить радость!\n\nСколько примерно шагов тебе удается пройти за день?",
                "Если нет времени на полноценную тренировку, подойдет микро-разминка. Пара потягиваний разгонят кровь.\n\nКак часто ты делаешь разминку в течение рабочего дня?"
            ])
                
        return JSONResponse({"response": mock_resp})

    user_data = {
        "name": user.name,
        "bmi": bmi,
        "current_weight": user.current_weight_kg,
        "target_weight": user.target_weight_kg,
        "goal_label": user.goal_label,
        "height_cm": user.height_cm
    }

    system_prompt = f"""Ты — продвинутый ИИ-консультант платформы "Step by Step".
Твоя цель — быть полезным спутником в мире здоровья, а не просто калькулятором ИМТ.

Контекст пользователя:
{json.dumps(user_data, ensure_ascii=False, indent=2)}

Правила работы:
1. Уйди от фиксации на ИМТ: Если пользователь уже получил совет про суставы и ИМТ, не повторяй это в каждом сообщении. Переходи к другим аспектам здоровья.
2. Разнообразие советов: Давай рекомендации по следующим темам:
   - Питание: Простые привычки (пить воду, замена сахара, полезные перекусы).
   - Психология: Как бороться с ленью, как не бросить тренировки, как хвалить себя за малые шаги.
   - Бытовая активность: Как сжигать калории незаметно (лестницы вместо лифта, прогулки во время звонков).
   - Сон и восстановление: Почему важно спать 7-8 часов для похудения.
3. Стиль общения: Пиши короткими, емкими блоками. Используй дружелюбный, но экспертный тон.
4. Интерактивность: В конце каждого совета задавай вовлекающий вопрос, не связанный напрямую с весом (например: "Как ты сегодня спал?" или "Какую полезную еду ты любишь больше всего?").
5. ЗАПРЕТЫ: Не используй фразу "[Демо-режим]" и не начинай каждый ответ с напоминания про "Алгоритм мягкого прогресса". Просто применяй его принципы в советах."""

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        ai_response = completion.choices[0].message.content
    except Exception as e:
        ai_response = f"Возникла ошибка при обращении к ИИ: {str(e)}"

    return JSONResponse({"response": ai_response})


@app.post("/update_weight")
def update_weight(
    request: Request,
    new_weight: float = Form(...),
    activity: str = Form("Взвешивание"),
    db: Session = Depends(get_db),
):
    """Record a new weight and update the user's current weight."""
    user = get_current_user(request, db)
    if user is None:
        return JSONResponse({"error": "Auth required"}, status_code=401)

    # Calculate daily % for this session (progress towards goal)
    pct = calculate_progress(user.start_weight_kg, new_weight, user.target_weight_kg)
    
    # Update user's current weight
    user.current_weight_kg = new_weight

    # Log the weighing event using the existing WorkoutLog structure
    log = WorkoutLog(
        user_id=user.id,
        activity=f"{activity} ({new_weight} кг)",
        duration_minutes=0,
        value=new_weight,
        progress_pct=pct,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    if request.headers.get("accept", "").startswith("application/json"):
        from fastapi.responses import JSONResponse
        bmi = calculate_bmi(new_weight, user.height_cm)
        motivation = get_motivation(pct)

        return JSONResponse({
            "pct": pct,
            "current_weight": new_weight,
            "target_weight": user.target_weight_kg,
            "bmi": bmi,
            "motivation": motivation,
            "log": {
                "activity": log.activity,
                "duration_minutes": 0,
                "value": new_weight,
                "progress_pct": int(log.progress_pct),
                "date": log.date.strftime('%d.%m %H:%M')
            }
        })

    return RedirectResponse("/", status_code=302)


@app.get("/reset")
def reset(db: Session = Depends(get_db)):
    """Factory reset — wipe all data."""
    db.query(WorkoutLog).delete()
    db.query(User).delete()
    db.commit()
    return RedirectResponse("/setup", status_code=302)


@app.get("/api/avatar_params")
def api_avatar_params(weight: float, height: float):
    """Simple API to compute avatar scale based on weight and height."""
    if height <= 0:
        return {"scale_x": 1.0}
    height_m = height / 100
    bmi = weight / (height_m * height_m)
    scale_x = 1.0 + (bmi - 22) * 0.05
    scale_x = max(0.6, min(scale_x, 2.5))
    return {"scale_x": round(scale_x, 2), "bmi": round(bmi, 1)}


@app.get("/leaderboard")
def get_leaderboard(request: Request, db: Session = Depends(get_db)):
    """Return top 10 users ranked by weight loss progress."""
    current_user = get_current_user(request, db)
    users = db.query(User).all()
    
    # Calculate progress for each user and sort
    ranked = []
    
    for u in users:
        pct = calculate_progress(u.start_weight_kg, u.current_weight_kg, u.target_weight_kg)
        ranked.append({
            "name": u.name,
            "progress_pct": int(pct),
            "is_me": current_user and u.id == current_user.id
        })
    
    # Sort descending by progress
    ranked.sort(key=lambda x: x["progress_pct"], reverse=True)
    return {"leaderboard": ranked[:10]}
