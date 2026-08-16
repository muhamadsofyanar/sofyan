
import os
import re
import secrets
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, Form, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import (
    create_engine, String, Text, Integer, Boolean, Date, DateTime, Numeric,
    ForeignKey, select, func, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_NAME = os.getenv("APP_NAME", "Sofyan OS")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sofyan_os.db")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-session-secret")
API_KEY = os.getenv("API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_CHAT_ID = os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "https://app.ruanglegalitas.com/api/telegram/webhook")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=connect_args)

class Base(DeclarativeBase): pass

class Area(Base):
    __tablename__ = "areas"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class InboxItem(Base):
    __tablename__ = "inbox_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    status: Mapped[str] = mapped_column(String(30), default="unprocessed")
    ai_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    name: Mapped[str] = mapped_column(String(255))
    desired_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mental_load: Mapped[int] = mapped_column(Integer, default=1)
    is_highlight: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class FinanceTransaction(Base):
    __tablename__ = "finance_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Debt(Base):
    __tablename__ = "debts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    contact_type: Mapped[str] = mapped_column(String(80), default="lead")
    stage: Mapped[str] = mapped_column(String(80), default="new")
    next_followup: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class ContentItem(Base):
    __tablename__ = "content_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    title: Mapped[str] = mapped_column(String(255))
    channel: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="idea")
    draft: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Dependency(Base):
    __tablename__ = "dependencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    waiting_for: Mapped[str] = mapped_column(String(255))
    next_followup_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="waiting")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

Base.metadata.create_all(engine)

def run_safe_migrations():
    """
    Lightweight idempotent migrations for upgrades from Sofyan OS v1/v2.
    SQLAlchemy create_all() creates new tables, but it does not add columns
    to tables that already exist.
    """
    statements = [
        "ALTER TABLE inbox_items ADD COLUMN IF NOT EXISTS ai_type VARCHAR(50)",
        "ALTER TABLE inbox_items ADD COLUMN IF NOT EXISTS ai_title VARCHAR(255)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS target_date DATE"
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

run_safe_migrations()

def get_db():
    with Session(engine) as s:
        yield s

def seed():
    with Session(engine) as s:
        if s.scalar(select(func.count(Area.id))) == 0:
            s.add_all([
                Area(code="personal", name="Pribadi"),
                Area(code="stifin", name="STIFIn"),
                Area(code="izinhukum", name="IZINHUKUM"),
            ])
            s.commit()
seed()

app = FastAPI(title=APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=False)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def rupiah(v):
    try: return "Rp{:,.0f}".format(float(v)).replace(",", ".")
    except Exception: return "Rp0"
templates.env.globals["rupiah"] = rupiah

def require_login(request: Request):
    if not request.session.get("user"): raise HTTPException(401)

def api_guard(x_api_key: Optional[str] = Header(None)):
    if not API_KEY or not secrets.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(401, "invalid api key")

@app.exception_handler(401)
async def unauthorized(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail":"unauthorized"}, status_code=401)
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request":request, "app_name":APP_NAME})

@app.post("/login")
def login(request: Request, username: str=Form(...), password: str=Form(...)):
    if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
        request.session["user"] = username
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request":request,"app_name":APP_NAME,"error":"Username atau password salah."}, status_code=401)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

def area_name_map(session):
    return {a.id:a.name for a in session.scalars(select(Area)).all()}

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session=Depends(get_db)):
    require_login(request)
    areas = session.scalars(select(Area).where(Area.is_active==True)).all()
    inbox = session.scalars(select(InboxItem).where(InboxItem.status=="unprocessed").order_by(InboxItem.created_at.desc()).limit(30)).all()
    tasks = session.scalars(select(Task).where(Task.status!="completed").order_by(Task.is_highlight.desc(), Task.mental_load.desc(), Task.created_at.desc())).all()
    projects = session.scalars(select(Project).where(Project.status=="active").order_by(Project.created_at.desc())).all()
    debts = session.scalars(select(Debt).where(Debt.status=="active")).all()
    contacts = session.scalars(select(Contact).order_by(Contact.next_followup.asc().nullslast(), Contact.created_at.desc()).limit(15)).all()
    content = session.scalars(select(ContentItem).order_by(ContentItem.created_at.desc()).limit(15)).all()
    knowledge = session.scalars(select(KnowledgeItem).order_by(KnowledgeItem.created_at.desc()).limit(10)).all()
    dependencies = session.scalars(select(Dependency).where(Dependency.status=="waiting").order_by(Dependency.next_followup_at.asc().nullslast())).all()

    income = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="income"))
    expense = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="expense"))
    debt_paid = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="debt_payment"))
    debt_balance = sum(float(d.current_balance) for d in debts)
    highlights = [t for t in tasks if t.is_highlight]
    amap = area_name_map(session)

    return templates.TemplateResponse("index.html", {
        "request":request,"app_name":APP_NAME,"areas":areas,"inbox":inbox,"tasks":tasks,"projects":projects,
        "debts":debts,"contacts":contacts,"content":content,"knowledge":knowledge,"dependencies":dependencies,
        "income":income,"expense":expense,"debt_paid":debt_paid,"debt_balance":debt_balance,"highlights":highlights,
        "amap":amap
    })

@app.post("/capture")
def capture(request:Request, text:str=Form(...), area_id:Optional[int]=Form(None), session:Session=Depends(get_db)):
    require_login(request)
    session.add(InboxItem(raw_text=text.strip(), area_id=area_id, source="manual"))
    session.commit()
    return RedirectResponse("/",303)

@app.post("/inbox/{item_id}/to-task")
def inbox_to_task(request:Request,item_id:int,session:Session=Depends(get_db)):
    require_login(request); item=session.get(InboxItem,item_id)
    if not item: raise HTTPException(404)
    if not item.area_id: return RedirectResponse("/?msg=area-required",303)
    session.add(Task(area_id=item.area_id,title=item.ai_title or item.raw_text)); item.status="task"; session.commit()
    return RedirectResponse("/",303)

@app.post("/inbox/{item_id}/someday")
def inbox_someday(request:Request,item_id:int,session:Session=Depends(get_db)):
    require_login(request); item=session.get(InboxItem,item_id)
    if not item: raise HTTPException(404)
    item.status="someday"; session.commit(); return RedirectResponse("/",303)

@app.post("/inbox/{item_id}/delete")
def inbox_delete(request:Request,item_id:int,session:Session=Depends(get_db)):
    require_login(request); item=session.get(InboxItem,item_id)
    if not item: raise HTTPException(404)
    item.status="deleted"; session.commit(); return RedirectResponse("/",303)

@app.post("/tasks")
def add_task(request:Request,title:str=Form(...),area_id:int=Form(...),project_id:Optional[int]=Form(None),
             scheduled_date:Optional[str]=Form(None),mental_load:int=Form(1),session:Session=Depends(get_db)):
    require_login(request)
    d=date.fromisoformat(scheduled_date) if scheduled_date else None
    session.add(Task(title=title.strip(),area_id=area_id,project_id=project_id or None,scheduled_date=d,mental_load=max(1,min(3,mental_load))))
    session.commit(); return RedirectResponse("/",303)

@app.post("/tasks/{task_id}/toggle-highlight")
def toggle_highlight(request:Request,task_id:int,session:Session=Depends(get_db)):
    require_login(request); task=session.get(Task,task_id)
    if not task: raise HTTPException(404)
    if not task.is_highlight:
        current=session.scalar(select(func.count(Task.id)).where(Task.is_highlight==True,Task.status!="completed"))
        if current>=3: return RedirectResponse("/?msg=max-highlight",303)
    task.is_highlight=not task.is_highlight; session.commit(); return RedirectResponse("/",303)

@app.post("/tasks/{task_id}/done")
def complete_task(request:Request,task_id:int,session:Session=Depends(get_db)):
    require_login(request); task=session.get(Task,task_id)
    if not task: raise HTTPException(404)
    task.status="completed"; task.is_highlight=False; task.completed_at=datetime.now(); session.commit(); return RedirectResponse("/",303)

@app.post("/projects")
def add_project(request:Request,name:str=Form(...),area_id:int=Form(...),desired_outcome:Optional[str]=Form(None),target_date:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    td=date.fromisoformat(target_date) if target_date else None
    session.add(Project(name=name.strip(),area_id=area_id,desired_outcome=desired_outcome,target_date=td)); session.commit()
    return RedirectResponse("/",303)

@app.post("/finance")
def add_finance(request:Request,type:str=Form(...),amount:Decimal=Form(...),area_id:int=Form(...),category:Optional[str]=Form(None),description:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    session.add(FinanceTransaction(type=type,amount=amount,area_id=area_id,category=category,description=description)); session.commit()
    return RedirectResponse("/",303)

@app.post("/debts")
def add_debt(request:Request,name:str=Form(...),original_amount:Decimal=Form(...),current_balance:Decimal=Form(...),notes:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    session.add(Debt(name=name.strip(),original_amount=original_amount,current_balance=current_balance,notes=notes)); session.commit()
    return RedirectResponse("/",303)

@app.post("/contacts")
def add_contact(request:Request,area_id:int=Form(...),name:str=Form(...),phone:Optional[str]=Form(None),contact_type:str=Form("lead"),stage:str=Form("new"),next_followup:Optional[str]=Form(None),notes:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    nf=datetime.fromisoformat(next_followup) if next_followup else None
    session.add(Contact(area_id=area_id,name=name,phone=phone,contact_type=contact_type,stage=stage,next_followup=nf,notes=notes)); session.commit()
    return RedirectResponse("/",303)

@app.post("/content")
def add_content(request:Request,area_id:int=Form(...),title:str=Form(...),channel:Optional[str]=Form(None),status:str=Form("idea"),draft:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    session.add(ContentItem(area_id=area_id,title=title,channel=channel,status=status,draft=draft)); session.commit()
    return RedirectResponse("/",303)

@app.post("/knowledge")
def add_knowledge(request:Request,title:str=Form(...),content:str=Form(...),area_id:Optional[int]=Form(None),category:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    session.add(KnowledgeItem(title=title,content=content,area_id=area_id or None,category=category)); session.commit()
    return RedirectResponse("/",303)

@app.post("/dependencies")
def add_dependency(request:Request,task_id:int=Form(...),waiting_for:str=Form(...),next_followup_at:Optional[str]=Form(None),notes:Optional[str]=Form(None),session:Session=Depends(get_db)):
    require_login(request)
    nf=datetime.fromisoformat(next_followup_at) if next_followup_at else None
    session.add(Dependency(task_id=task_id,waiting_for=waiting_for,next_followup_at=nf,notes=notes)); session.commit()
    return RedirectResponse("/",303)

def _area_from_words(session:Session,text:str):
    t=text.lower(); code=None
    if any(x in t for x in ["izinhukum","izin hukum","legalitas"]): code="izinhukum"
    elif any(x in t for x in ["stifin","promotor","genetic"]): code="stifin"
    elif any(x in t for x in ["pribadi","keluarga","personal","kuliah","alquran","al-qur'an"]): code="personal"
    return session.scalar(select(Area).where(Area.code==code)) if code else None

def _parse_amount(raw:str):
    s=raw.lower().replace("rp","").replace(" ",""); mult=1
    if s.endswith("rb"): mult,s=1000,s[:-2]
    elif s.endswith("ribu"): mult,s=1000,s[:-4]
    elif s.endswith("jt"): mult,s=1000000,s[:-2]
    elif s.endswith("juta"): mult,s=1000000,s[:-4]
    s=s.replace(".","").replace(",",".")
    try:return Decimal(str(float(s)*mult))
    except:return None

def _finance_from_text(text:str):
    low=text.strip().lower()
    patterns=[
      ("debt_payment",r"^(?:bayar\s+utang|cicil\s+utang)\s+([0-9][0-9.,]*(?:rb|ribu|jt|juta)?)\s*(.*)$"),
      ("expense",r"^(?:keluar|pengeluaran|belanja)\s+([0-9][0-9.,]*(?:rb|ribu|jt|juta)?)\s*(.*)$"),
      ("income",r"^(?:masuk|pemasukan|terima)\s+([0-9][0-9.,]*(?:rb|ribu|jt|juta)?)\s*(.*)$")
    ]
    for typ,pat in patterns:
        m=re.match(pat,low,re.I)
        if m:
            amt=_parse_amount(m.group(1))
            if amt is not None:return typ,amt,(m.group(2) or "").strip()
    return None

def _ai_classify(text:str):
    if not OPENAI_API_KEY or OpenAI is None: return None
    try:
        client=OpenAI(api_key=OPENAI_API_KEY)
        prompt=f"""Klasifikasikan input untuk Sofyan OS.
Pilihan type: task, project_candidate, idea, knowledge, dependency, finance, someday.
Jangan paksa ke task jika masih berupa keinginan/ide.
Keluarkan JSON saja dengan keys: type,title,area.
area hanya personal, stifin, izinhukum, unknown.
Input: {text}"""
        r=client.responses.create(model=OPENAI_MODEL,input=prompt)
        import json
        return json.loads(r.output_text)
    except Exception:
        return None

async def _telegram_send(chat_id:str,text:str):
    if not TELEGRAM_BOT_TOKEN:return
    async with httpx.AsyncClient(timeout=15) as c:
        try: await c.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",json={"chat_id":chat_id,"text":text})
        except: pass

@app.post("/api/capture",dependencies=[Depends(api_guard)])
async def api_capture(request:Request,session:Session=Depends(get_db)):
    data=await request.json(); text=(data.get("text") or "").strip()
    if not text:raise HTTPException(400,"text required")
    area=None
    if data.get("area"): area=session.scalar(select(Area).where(Area.code==data["area"]))
    item=InboxItem(raw_text=text,area_id=area.id if area else None,source=data.get("source","api"))
    ai=_ai_classify(text)
    if ai:
        item.ai_type=ai.get("type"); item.ai_title=ai.get("title")
    session.add(item); session.commit(); return {"ok":True,"id":item.id,"ai":ai}

@app.get("/api/health")
def health(): return {"ok":True,"app":APP_NAME}

@app.post("/api/telegram/setup",dependencies=[Depends(api_guard)])
async def telegram_setup():
    if not TELEGRAM_BOT_TOKEN:raise HTTPException(400,"TELEGRAM_BOT_TOKEN belum diisi")
    payload={"url":TELEGRAM_WEBHOOK_URL}
    if TELEGRAM_WEBHOOK_SECRET: payload["secret_token"]=TELEGRAM_WEBHOOK_SECRET
    async with httpx.AsyncClient(timeout=20) as c:
        r=await c.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",json=payload)
    return r.json()

@app.post("/api/telegram/webhook")
async def telegram_webhook(request:Request,session:Session=Depends(get_db),x_telegram_bot_api_secret_token:Optional[str]=Header(None)):
    data=await request.json(); msg=data.get("message") or {}; chat=msg.get("chat") or {}; chat_id=str(chat.get("id") or ""); text=(msg.get("text") or "").strip()
    if not chat_id or not text:return {"ok":True}
    if TELEGRAM_ALLOWED_CHAT_ID and chat_id!=str(TELEGRAM_ALLOWED_CHAT_ID):return {"ok":True,"ignored":True}
    if text.lower() in {"/start","/help"}:
        await _telegram_send(chat_id,"Sofyan OS aktif.\nCatatan biasa → Inbox.\nkeluar 85rb bensin pribadi → pengeluaran.\nmasuk 1jt izinhukum closing PT → pemasukan.\nbayar utang 500rb pribadi → pembayaran utang.")
        return {"ok":True}
    fin=_finance_from_text(text); area=_area_from_words(session,text)
    if fin:
        typ,amt,desc=fin
        if not area: area=session.scalar(select(Area).where(Area.code=="personal"))
        tx=FinanceTransaction(type=typ,amount=amt,area_id=area.id,description=desc or text);session.add(tx);session.commit()
        await _telegram_send(chat_id,f"✓ Tercatat {rupiah(amt)} · {area.name}")
        return {"ok":True,"kind":"finance","id":tx.id}
    ai=_ai_classify(text)
    if ai and ai.get("area") in {"personal","stifin","izinhukum"}:
        a=session.scalar(select(Area).where(Area.code==ai["area"]))
        if a: area=a
    item=InboxItem(raw_text=text,area_id=area.id if area else None,source="telegram",ai_type=(ai or {}).get("type"),ai_title=(ai or {}).get("title"))
    session.add(item);session.commit()
    hint=f" · AI: {item.ai_type}" if item.ai_type else ""
    await _telegram_send(chat_id,f"✓ Masuk Inbox{hint}\n{text}")
    return {"ok":True,"kind":"inbox","id":item.id}

@app.get("/api/daily-review",dependencies=[Depends(api_guard)])
def daily_review(session:Session=Depends(get_db)):
    inbox=session.scalars(select(InboxItem).where(InboxItem.status=="unprocessed").order_by(InboxItem.created_at.asc()).limit(30)).all()
    tasks=session.scalars(select(Task).where(Task.status!="completed").order_by(Task.mental_load.desc(),Task.created_at.asc()).limit(20)).all()
    deps=session.scalars(select(Dependency).where(Dependency.status=="waiting")).all()
    return {
        "inbox":[{"id":x.id,"text":x.raw_text,"ai_type":x.ai_type} for x in inbox],
        "candidate_highlights":[{"id":t.id,"title":t.title,"mental_load":t.mental_load} for t in tasks],
        "dependencies":[{"id":d.id,"waiting_for":d.waiting_for,"next_followup_at":d.next_followup_at} for d in deps]
    }

@app.get("/api/executive-summary",dependencies=[Depends(api_guard)])
def executive_summary(session:Session=Depends(get_db)):
    income=float(session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="income")))
    expense=float(session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="expense")))
    debt_paid=float(session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="debt_payment")))
    debt_balance=sum(float(x.current_balance) for x in session.scalars(select(Debt).where(Debt.status=="active")).all())
    return {
        "highlights":session.scalar(select(func.count(Task.id)).where(Task.is_highlight==True,Task.status!="completed")),
        "open_tasks":session.scalar(select(func.count(Task.id)).where(Task.status!="completed")),
        "inbox":session.scalar(select(func.count(InboxItem.id)).where(InboxItem.status=="unprocessed")),
        "active_projects":session.scalar(select(func.count(Project.id)).where(Project.status=="active")),
        "contacts":session.scalar(select(func.count(Contact.id))),
        "content_pipeline":session.scalar(select(func.count(ContentItem.id)).where(ContentItem.status!="published")),
        "knowledge":session.scalar(select(func.count(KnowledgeItem.id))),
        "cashflow":income-expense-debt_paid,
        "debt_balance":debt_balance
    }


@app.post("/api/finance", dependencies=[Depends(api_guard)])
async def api_finance(request: Request, session: Session = Depends(get_db)):
    data = await request.json()
    typ = data.get("type")
    if typ not in {"income","expense","debt_payment"}:
        raise HTTPException(400, "type invalid")
    area = session.scalar(select(Area).where(Area.code == data.get("area","personal")))
    if not area:
        raise HTTPException(400, "area invalid")
    try:
        amount = Decimal(str(data.get("amount")))
    except Exception:
        raise HTTPException(400, "amount invalid")
    tx = FinanceTransaction(
        type=typ, amount=amount, area_id=area.id,
        category=data.get("category"), description=data.get("description")
    )
    session.add(tx); session.commit()
    return {"ok":True,"id":tx.id}

@app.post("/api/crm/upsert", dependencies=[Depends(api_guard)])
async def api_crm_upsert(request: Request, session: Session = Depends(get_db)):
    data = await request.json()
    area = session.scalar(select(Area).where(Area.code == data.get("area","izinhukum")))
    if not area: raise HTTPException(400, "area invalid")
    phone = (data.get("phone") or "").strip()
    name = (data.get("name") or phone or "Tanpa Nama").strip()
    q = select(Contact).where(Contact.area_id == area.id)
    if phone:
        q = q.where(Contact.phone == phone)
    else:
        q = q.where(Contact.name == name)
    c = session.scalar(q)
    if not c:
        c = Contact(area_id=area.id, name=name, phone=phone or None)
        session.add(c)
    c.contact_type = data.get("contact_type", c.contact_type or "lead")
    c.stage = data.get("stage", c.stage or "new")
    c.notes = data.get("notes", c.notes)
    if data.get("next_followup"):
        try: c.next_followup = datetime.fromisoformat(data["next_followup"])
        except: pass
    session.commit()
    return {"ok":True,"id":c.id}

@app.post("/api/content", dependencies=[Depends(api_guard)])
async def api_content(request: Request, session: Session = Depends(get_db)):
    data = await request.json()
    area = session.scalar(select(Area).where(Area.code == data.get("area","personal")))
    if not area: raise HTTPException(400, "area invalid")
    item = ContentItem(
        area_id=area.id,
        title=(data.get("title") or "Untitled").strip(),
        channel=data.get("channel"),
        status=data.get("status","idea"),
        draft=data.get("draft")
    )
    session.add(item); session.commit()
    return {"ok":True,"id":item.id}

@app.post("/api/knowledge", dependencies=[Depends(api_guard)])
async def api_knowledge(request: Request, session: Session = Depends(get_db)):
    data = await request.json()
    area = None
    if data.get("area"):
        area = session.scalar(select(Area).where(Area.code == data["area"]))
    item = KnowledgeItem(
        area_id=area.id if area else None,
        title=(data.get("title") or "Catatan").strip(),
        content=(data.get("content") or "").strip(),
        category=data.get("category")
    )
    if not item.content: raise HTTPException(400, "content required")
    session.add(item); session.commit()
    return {"ok":True,"id":item.id}

@app.post("/api/starsender/inbound")
async def starsender_inbound(request: Request, session: Session = Depends(get_db)):
    # Endpoint ini sengaja menerima payload StarSender langsung.
    data = await request.json()
    message = (data.get("message") or "").strip()
    sender = str(data.get("from") or "").strip()
    device_name = str(data.get("device_name") or data.get("device") or "").lower()
    push_name = (data.get("push_name") or sender or "Lead WhatsApp").strip()
    if not message:
        return {"ok":True,"ignored":True}

    if "stifin" in device_name:
        area_code = "stifin"
    elif any(x in device_name for x in ["izin","legal","hukum"]):
        area_code = "izinhukum"
    else:
        area_code = "personal"

    area = session.scalar(select(Area).where(Area.code == area_code))

    # Business WhatsApp becomes CRM contact + captured inbox item.
    if area_code in {"stifin","izinhukum"}:
        contact = session.scalar(select(Contact).where(Contact.area_id==area.id, Contact.phone==sender))
        if not contact:
            contact = Contact(
                area_id=area.id, name=push_name, phone=sender,
                contact_type="lead", stage="new",
                notes=f"Masuk dari StarSender. Pesan terakhir: {message[:500]}"
            )
            session.add(contact)
        else:
            contact.notes = f"Pesan terakhir: {message[:500]}"
        item = InboxItem(
            area_id=area.id, raw_text=f"WA {push_name} ({sender}): {message}",
            source="whatsapp", status="unprocessed"
        )
        ai = _ai_classify(message)
        if ai:
            item.ai_type = ai.get("type"); item.ai_title = ai.get("title")
        session.add(item); session.commit()
        return {"ok":True,"area":area_code,"contact_id":contact.id,"inbox_id":item.id}

    item = InboxItem(area_id=area.id, raw_text=f"WA {push_name}: {message}", source="whatsapp")
    session.add(item); session.commit()
    return {"ok":True,"area":"personal","inbox_id":item.id}

@app.get("/api/crm/followups", dependencies=[Depends(api_guard)])
def api_crm_followups(session: Session = Depends(get_db)):
    now = datetime.now()
    rows = session.scalars(
        select(Contact).where(Contact.next_followup != None, Contact.next_followup <= now + timedelta(days=1))
        .order_by(Contact.next_followup.asc())
    ).all()
    amap = area_name_map(session)
    return [{"id":c.id,"name":c.name,"phone":c.phone,"area":amap.get(c.area_id),"stage":c.stage,
             "next_followup":c.next_followup.isoformat() if c.next_followup else None} for c in rows]
