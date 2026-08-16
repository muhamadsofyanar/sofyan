import os
import secrets
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, Depends, Form, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import (
    create_engine, String, Text, Integer, Boolean, Date, DateTime, Numeric,
    ForeignKey, select, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

APP_NAME = os.getenv("APP_NAME", "Sofyan OS")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sofyan_os.db")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-session-secret")
API_KEY = os.getenv("API_KEY", "")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=connect_args)

class Base(DeclarativeBase):
    pass

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    name: Mapped[str] = mapped_column(String(255))
    desired_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
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

Base.metadata.create_all(engine)

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
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def rupiah(v):
    try:
        return "Rp{:,.0f}".format(float(v)).replace(",", ".")
    except Exception:
        return "Rp0"

templates.env.globals["rupiah"] = rupiah

def require_login(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401)

def api_guard(x_api_key: Optional[str] = Header(None)):
    if not API_KEY or not secrets.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(status_code=401, detail="invalid api key")

@app.exception_handler(401)
async def unauthorized(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "app_name": APP_NAME})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
        request.session["user"] = username
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "app_name": APP_NAME, "error": "Username atau password salah."},
        status_code=401,
    )

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_db)):
    require_login(request)
    areas = session.scalars(select(Area).where(Area.is_active == True)).all()
    inbox = session.scalars(
        select(InboxItem).where(InboxItem.status == "unprocessed").order_by(InboxItem.created_at.desc()).limit(20)
    ).all()
    tasks = session.scalars(
        select(Task).where(Task.status != "completed")
        .order_by(Task.is_highlight.desc(), Task.scheduled_date.asc().nullslast(), Task.mental_load.desc(), Task.created_at.desc())
    ).all()
    projects = session.scalars(select(Project).where(Project.status == "active").order_by(Project.created_at.desc())).all()
    debts = session.scalars(select(Debt).where(Debt.status == "active")).all()
    txs = session.scalars(select(FinanceTransaction).order_by(FinanceTransaction.transaction_date.desc()).limit(15)).all()

    income = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="income"))
    expense = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="expense"))
    debt_paid = session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount),0)).where(FinanceTransaction.type=="debt_payment"))
    debt_balance = sum(float(d.current_balance) for d in debts)
    highlights = [t for t in tasks if t.is_highlight]

    return templates.TemplateResponse("index.html", {
        "request": request, "app_name": APP_NAME,
        "areas": areas, "inbox": inbox, "tasks": tasks, "projects": projects,
        "debts": debts, "txs": txs,
        "income": income, "expense": expense, "debt_paid": debt_paid,
        "debt_balance": debt_balance, "highlights": highlights,
    })

@app.post("/capture")
def capture(request: Request, text: str = Form(...), area_id: Optional[int] = Form(None), session: Session = Depends(get_db)):
    require_login(request)
    session.add(InboxItem(raw_text=text.strip(), area_id=area_id, source="manual"))
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/inbox/{item_id}/to-task")
def inbox_to_task(request: Request, item_id: int, session: Session = Depends(get_db)):
    require_login(request)
    item = session.get(InboxItem, item_id)
    if not item:
        raise HTTPException(404)
    if not item.area_id:
        return RedirectResponse("/?msg=area-required", status_code=303)
    session.add(Task(area_id=item.area_id, title=item.raw_text))
    item.status = "task"
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/inbox/{item_id}/someday")
def inbox_someday(request: Request, item_id: int, session: Session = Depends(get_db)):
    require_login(request)
    item = session.get(InboxItem, item_id)
    if not item:
        raise HTTPException(404)
    item.status = "someday"
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/inbox/{item_id}/delete")
def inbox_delete(request: Request, item_id: int, session: Session = Depends(get_db)):
    require_login(request)
    item = session.get(InboxItem, item_id)
    if not item:
        raise HTTPException(404)
    item.status = "deleted"
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/tasks")
def add_task(
    request: Request,
    title: str = Form(...),
    area_id: int = Form(...),
    project_id: Optional[int] = Form(None),
    scheduled_date: Optional[str] = Form(None),
    mental_load: int = Form(1),
    session: Session = Depends(get_db),
):
    require_login(request)
    d = date.fromisoformat(scheduled_date) if scheduled_date else None
    session.add(Task(
        title=title.strip(), area_id=area_id,
        project_id=project_id or None,
        scheduled_date=d, mental_load=max(1, min(3, mental_load))
    ))
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/tasks/{task_id}/toggle-highlight")
def toggle_highlight(request: Request, task_id: int, session: Session = Depends(get_db)):
    require_login(request)
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(404)
    if not task.is_highlight:
        current = session.scalar(select(func.count(Task.id)).where(Task.is_highlight == True, Task.status != "completed"))
        if current >= 3:
            return RedirectResponse("/?msg=max-highlight", status_code=303)
    task.is_highlight = not task.is_highlight
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/tasks/{task_id}/done")
def complete_task(request: Request, task_id: int, session: Session = Depends(get_db)):
    require_login(request)
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(404)
    task.status = "completed"
    task.is_highlight = False
    task.completed_at = datetime.now()
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/projects")
def add_project(request: Request, name: str = Form(...), area_id: int = Form(...), desired_outcome: Optional[str] = Form(None), session: Session = Depends(get_db)):
    require_login(request)
    session.add(Project(name=name.strip(), area_id=area_id, desired_outcome=desired_outcome))
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/finance")
def add_finance(
    request: Request,
    type: str = Form(...), amount: Decimal = Form(...),
    area_id: int = Form(...), category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    session: Session = Depends(get_db)
):
    require_login(request)
    if type not in {"income","expense","debt_payment"}:
        raise HTTPException(400)
    session.add(FinanceTransaction(type=type, amount=amount, area_id=area_id, category=category, description=description))
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/debts")
def add_debt(
    request: Request,
    name: str = Form(...), original_amount: Decimal = Form(...),
    current_balance: Decimal = Form(...), notes: Optional[str] = Form(None),
    session: Session = Depends(get_db)
):
    require_login(request)
    session.add(Debt(name=name.strip(), original_amount=original_amount, current_balance=current_balance, notes=notes))
    session.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/api/capture", dependencies=[Depends(api_guard)])
async def api_capture(request: Request, session: Session = Depends(get_db)):
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text required")
    area_id = None
    if data.get("area"):
        area = session.scalar(select(Area).where(Area.code == data["area"]))
        area_id = area.id if area else None
    item = InboxItem(raw_text=text, area_id=area_id, source=data.get("source","api"))
    session.add(item)
    session.commit()
    return {"ok": True, "id": item.id}

@app.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME}
