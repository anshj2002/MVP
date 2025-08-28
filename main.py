
import json, os, random, string
from pathlib import Path
from fastapi import FastAPI, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates

from store import STORE

APP_ROOT = Path(__file__).parent
DATA_PATH = APP_ROOT / "data" / "questions.json"

with open(DATA_PATH, "r") as f:
    QUESTIONS = json.load(f)

app = FastAPI(title="Economics MCQ MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(APP_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_ROOT / "templates"))

def new_sid(n=24):
    import secrets
    return secrets.token_hex(n//2)

def pick_question(level:int, history_ids:set):
    # Map levels to difficulty bias
    # 1-3: prefer easy; 4-6: medium; 7-10: hard
    if level <= 3:
        preferred = "easy"
    elif level <= 6:
        preferred = "medium"
    else:
        preferred = "hard"
    candidates = [q for q in QUESTIONS if q["difficulty"] == preferred and q["id"] not in history_ids]
    if not candidates:
        candidates = [q for q in QUESTIONS if q["id"] not in history_ids]
    if not candidates:
        return None
    return random.choice(candidates)

@app.middleware("http")
async def ensure_sid(request: Request, call_next):
    sid = request.cookies.get("sid")
    if not sid:
        sid = new_sid()
        response = await call_next(request)
        response.set_cookie("sid", sid, httponly=True, samesite="lax", max_age=60*60*24*7)
        return response
    else:
        response = await call_next(request)
        return response

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/quiz", response_class=HTMLResponse)
async def quiz(request: Request):
    sid = request.cookies.get("sid")
    session = STORE.get(sid)
    history_ids = set(a["qid"] for a in session["answers"])
    q = pick_question(session["level"], history_ids)
    return templates.TemplateResponse("quiz.html", {"request": request, "question": q, "session": session})

@app.post("/submit")
async def submit(request: Request, qid: str = Form(...), answer: int = Form(...)):
    sid = request.cookies.get("sid")
    session = STORE.get(sid)
    q = next((x for x in QUESTIONS if x["id"] == qid), None)
    if not q:
        return RedirectResponse("/quiz", status_code=302)
    correct = int(answer) == int(q["answer_index"])
    STORE.record_answer(sid, qid, correct, q["difficulty"], q["topic"])
    return RedirectResponse("/quiz?just_answered=" + ("1" if correct else "0"), status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    sid = request.cookies.get("sid")
    summary = STORE.summary(sid)
    return templates.TemplateResponse("dashboard.html", {"request": request, "summary": summary})

@app.get("/api/progress")
async def api_progress(request: Request):
    sid = request.cookies.get("sid")
    summary = STORE.summary(sid)
    return JSONResponse(summary)
