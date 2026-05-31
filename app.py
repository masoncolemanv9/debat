import os
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

# Участники дебатов: имя -> модель в OpenRouter.
# Можешь менять модели или добавлять своих участников.
DEBATERS = {
    "Grok": "x-ai/grok-3",
    "GPT-4o": "openai/gpt-4o",
    "Claude": "anthropic/claude-3.5-sonnet",
}


def ask(model, system, transcript, name):
    user_msg = (
        "Ход дебатов на данный момент:\n\n"
        + (transcript or "(пока никто не высказался)")
        + f"\n\nТеперь твоя реплика, {name}. Кратко, 3-5 предложений."
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 500,
    }
    try:
        r = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=120,
        )
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Ошибка модели {name}: {e}]"


def run_debate(topic, rounds):
    transcript = ""
    log = []
    for rnd in range(1, rounds + 1):
        for name, model in DEBATERS.items():
            system = (
                f"Ты участник дебатов по имени {name}. "
                f"Тема дебатов: «{topic}». "
                "Отстаивай свою позицию, спорь с оппонентами, "
                "будь убедительным, но кратким."
            )
            reply = ask(model, system, transcript, name)
            transcript += f"\n\n{name}: {reply}"
            log.append((rnd, name, reply))
    return log


FORM = """
<html><head><meta charset="utf-8"><title>Дебаты ИИ</title>
<style>
 body{font-family:sans-serif;max-width:760px;margin:40px auto;padding:0 16px}
 input,button{font-size:16px;padding:8px;margin:4px 0}
 input[type=text]{width:100%}
 .bubble{border-radius:12px;padding:12px 16px;margin:10px 0}
 .name{font-weight:bold;margin-bottom:4px}
</style></head><body>
<h1>🤖 Дебаты ИИ</h1>
<form method="post" action="/debate">
  <label>Тема дебатов:</label><br>
  <input type="text" name="topic" placeholder="Например: Стоит ли колонизировать Марс?" required><br>
  <label>Сколько раундов:</label>
  <input type="number" name="rounds" value="2" min="1" max="5"><br>
  <button type="submit">Начать дебаты</button>
</form>
</body></html>
"""

COLORS = {"Grok": "#e8f0fe", "GPT-4o": "#e6f4ea", "Claude": "#fdedeb"}


@app.get("/", response_class=HTMLResponse)
def home():
    return FORM


@app.post("/debate", response_class=HTMLResponse)
def debate(topic: str = Form(...), rounds: int = Form(2)):
    log = run_debate(topic, rounds)
    html = f"<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;max-width:760px;margin:40px auto;padding:0 16px'>"
    html += f"<h1>🤖 Дебаты: {topic}</h1>"
    for rnd, name, reply in log:
        color = COLORS.get(name, "#f0f0f0")
        html += (
            f"<div style='background:{color};border-radius:12px;padding:12px 16px;margin:10px 0'>"
            f"<div style='font-weight:bold'>Раунд {rnd} — {name}</div>"
            f"<div>{reply}</div></div>"
        )
    html += "<br><a href='/'>← Новая тема</a></body></html>"
    return html
