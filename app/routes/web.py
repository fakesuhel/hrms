from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.utils.auth import get_current_user_optional
from app.database.users import UserInDB
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
async def login_page(request: Request, current_user: UserInDB = Depends(get_current_user_optional)):
    """Serve the login page or redirect based on department"""
    if current_user:
        # User is already logged in, redirect based on department and role
        department = getattr(current_user, 'department', '').lower()
        role = getattr(current_user, 'role', '').lower()
        
        if department == 'sales':
            return RedirectResponse(url="/app/sales/dashboard")
        elif department == 'management' and role in ['hr', 'admin', 'director']:
            return RedirectResponse(url="/app/hr/dashboard")
        elif department == 'development':
            return RedirectResponse(url="/app/it/dashboard")
        else:
            # Default redirect
            return RedirectResponse(url="/app/sales/dashboard")
    
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

@router.get("/app/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Serve the general settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/app/leave-requests", response_class=HTMLResponse)
async def leave_requests_page(request: Request):
    """Serve the general leave requests page"""
    return templates.TemplateResponse("shared/leave-requests.html", {"request": request})

@router.get("/app/js/{filename}")
async def serve_js(filename: str):
    """Serve JavaScript files"""
    file_path = web_dir / "js" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"JavaScript file {filename} not found")
    return FileResponse(file_path)

@router.get("/static/js/{filename}")
async def serve_static_js(filename: str):
    """Serve static JavaScript files"""
    file_path = Path("./app/static/js") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Static JavaScript file {filename} not found")
    return FileResponse(file_path)

@router.get("/static/css/{filename}")
async def serve_static_css(filename: str):
    """Serve static CSS files"""
    file_path = Path("./app/static/css") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Static CSS file {filename} not found")
    return FileResponse(file_path)

# Sales Department Routes
@router.get("/app/sales/dashboard", response_class=HTMLResponse)
async def sales_dashboard_page(request: Request):
    """Serve the sales dashboard page"""
    return templates.TemplateResponse("departments/sales/dashboard.html", {"request": request})

@router.get("/app/sales/attendance", response_class=HTMLResponse)
async def sales_attendance_page(request: Request):
    """Serve the sales attendance page"""
    return templates.TemplateResponse("departments/sales/attendance.html", {"request": request})

@router.get("/app/sales/leads", response_class=HTMLResponse)
async def sales_leads_page(request: Request):
    """Serve the sales leads page"""
    return templates.TemplateResponse("departments/sales/leads.html", {"request": request})

@router.get("/app/sales/customers", response_class=HTMLResponse)
async def sales_customers_page(request: Request):
    """Serve the sales customers page"""
    return templates.TemplateResponse("departments/sales/customers.html", {"request": request})

@router.get("/app/sales/reports", response_class=HTMLResponse)
async def sales_reports_page(request: Request):
    """Serve the sales reports page"""
    return templates.TemplateResponse("departments/sales/reports.html", {"request": request})

@router.get("/app/sales/profile", response_class=HTMLResponse)
async def sales_profile_page(request: Request):
    """Serve the sales profile page"""
    return templates.TemplateResponse("departments/sales/profile.html", {"request": request})

@router.get("/app/sales/leave-requests", response_class=HTMLResponse)
async def sales_leave_requests_page(request: Request):
    """Serve the sales leave requests page"""
    return templates.TemplateResponse("departments/sales/leave-requests.html", {"request": request})

@router.get("/app/sales/performance", response_class=HTMLResponse)
async def sales_performance_page(request: Request):
    """Serve the sales performance page"""
    return templates.TemplateResponse("departments/sales/performance.html", {"request": request})

@router.get("/app/sales/team", response_class=HTMLResponse)
async def sales_team_page(request: Request):
    """Serve the sales team page"""
    return templates.TemplateResponse("departments/sales/team.html", {"request": request})

@router.get("/app/sales/daily-reports", response_class=HTMLResponse)
async def sales_daily_reports_page(request: Request):
    """Serve the sales daily reports page"""
    return templates.TemplateResponse("departments/sales/daily-reports.html", {"request": request})

@router.get("/app/sales/penalties", response_class=HTMLResponse)
async def sales_penalties_page(request: Request):
    """Serve the sales penalties page"""
    return templates.TemplateResponse("departments/sales/penalties.html", {"request": request})

@router.get("/app/sales/settings", response_class=HTMLResponse)
async def sales_settings_page(request: Request):
    """Serve the sales settings page (manager access)"""
    return templates.TemplateResponse("departments/sales/settings.html", {"request": request})

# HR Department Routes
@router.get("/app/hr/dashboard", response_class=HTMLResponse)
async def hr_dashboard_page(request: Request):
    """Serve the HR dashboard page"""
    return templates.TemplateResponse("departments/hr/dashboard.html", {"request": request})

@router.get("/app/hr/attendance", response_class=HTMLResponse)
async def hr_attendance_page(request: Request):
    """Serve the HR attendance page"""
    return templates.TemplateResponse("departments/hr/attendance.html", {"request": request})

@router.get("/app/hr/employees", response_class=HTMLResponse)
async def hr_employees_page(request: Request):
    """Serve the HR employees page"""
    return templates.TemplateResponse("departments/hr/employees.html", {"request": request})

@router.get("/app/hr/payroll", response_class=HTMLResponse)
async def hr_payroll_main_page(request: Request):
    """Serve the HR payroll page"""
    return templates.TemplateResponse("departments/hr/payroll.html", {"request": request})


@router.get("/app/hr/recruitment", response_class=HTMLResponse)
async def hr_recruitment_page(request: Request):
    """Serve the HR recruitment page"""
    return templates.TemplateResponse("departments/hr/recruitment.html", {"request": request})

@router.get("/app/hr/leave-requests", response_class=HTMLResponse)
async def hr_leave_requests_page(request: Request):
    """Serve the HR leave requests page"""
    return templates.TemplateResponse("departments/hr/leave-requests.html", {"request": request})

@router.get("/app/hr/performance", response_class=HTMLResponse)
async def hr_performance_page(request: Request):
    """Serve the HR performance page"""
    return templates.TemplateResponse("departments/hr/performance-reviews.html", {"request": request})

@router.get("/app/hr/reports", response_class=HTMLResponse)
async def hr_reports_page(request: Request):
    """Serve the HR reports page"""
    return templates.TemplateResponse("departments/hr/reports.html", {"request": request})

@router.get("/app/hr/settings", response_class=HTMLResponse)
async def hr_settings_page(request: Request):
    """Serve the HR settings page"""
    return templates.TemplateResponse("departments/hr/settings.html", {"request": request})

@router.get("/app/hr/profile", response_class=HTMLResponse)
async def hr_profile_page(request: Request):
    """Serve the HR profile page"""
    return templates.TemplateResponse("departments/hr/profile.html", {"request": request})

# IT Department Routes  
@router.get("/app/it/dashboard", response_class=HTMLResponse)
async def it_dashboard_page(request: Request):
    """Serve the IT dashboard page"""
    return templates.TemplateResponse("departments/development/dashboard.html", {"request": request})

@router.get("/app/it/attendance", response_class=HTMLResponse)
async def it_attendance_page(request: Request):
    """Serve the IT attendance page"""
    return templates.TemplateResponse("departments/development/attendance.html", {"request": request})

@router.get("/app/it/projects", response_class=HTMLResponse)
async def it_projects_page(request: Request):
    """Serve the IT projects page"""
    return templates.TemplateResponse("departments/development/projects.html", {"request": request})


@router.get("/app/it/daily-reports", response_class=HTMLResponse)
async def it_daily_reports_page(request: Request):
    """Serve the IT daily reports page"""
    return templates.TemplateResponse("departments/development/daily-reports.html", {"request": request})

@router.get("/app/it/team", response_class=HTMLResponse)
async def it_team_page(request: Request):
    """Serve the IT team page"""
    return templates.TemplateResponse("departments/development/team.html", {"request": request})

@router.get("/app/it/performance", response_class=HTMLResponse)
async def it_performance_page(request: Request):
    """Serve the IT performance page"""
    return templates.TemplateResponse("departments/development/performance-reviews.html", {"request": request})

@router.get("/app/it/leave-requests", response_class=HTMLResponse)
async def it_leave_requests_page(request: Request):
    """Serve the IT leave requests page"""
    return templates.TemplateResponse("departments/development/leave-requests.html", {"request": request})

@router.get("/app/it/profile", response_class=HTMLResponse)
async def it_profile_page(request: Request):
    """Serve the IT profile page"""
    return templates.TemplateResponse("departments/development/profile.html", {"request": request})

@router.get("/app/it/penalties", response_class=HTMLResponse)
async def it_penalties_page(request: Request):
    """Serve the IT penalties page"""
    return templates.TemplateResponse("departments/development/penalties.html", {"request": request})

@router.get("/app/it/reports", response_class=HTMLResponse)
async def it_reports_page(request: Request):
    """Serve the IT reports page (manager access)"""
    return templates.TemplateResponse("departments/development/reports.html", {"request": request})

@router.get("/app/it/settings", response_class=HTMLResponse)
async def it_settings_page(request: Request):
    """Serve the IT settings page (manager access)"""
    return templates.TemplateResponse("departments/development/settings.html", {"request": request})