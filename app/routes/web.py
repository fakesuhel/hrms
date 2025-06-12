from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

router = APIRouter(tags=["web"])

# Path to web files
BASE_DIR = Path(__file__).resolve().parent.parent
web_dir = "./app/web"
templates = Jinja2Templates(directory=str(web_dir))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the index page (redirect to login)"""
    return RedirectResponse(url="/app/login")

@router.get("/app/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/app/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/app/attendance", response_class=HTMLResponse)
async def attendance_page(request: Request):
    """Serve the attendance page"""
    return templates.TemplateResponse("attendance.html", {"request": request})

@router.get("/app/project", response_class=HTMLResponse)
async def project_page(request: Request):
    """Serve the attendance page"""
    return templates.TemplateResponse("projects.html", {"request": request})

@router.get("/app/reports", response_class=HTMLResponse)
async def daily_reports(request: Request):
    """Serve the attendance page"""
    return templates.TemplateResponse("daily-reports.html", {"request": request})

@router.get("/app/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    """Serve the teams page"""
    return templates.TemplateResponse("teams.html", {"request": request})

@router.get("/app/js/{filename}")
async def serve_js(filename: str):
    """Serve JavaScript files"""
    file_path = web_dir / "js" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"JavaScript file {filename} not found")
    return FileResponse(file_path)