from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.utils.auth import get_current_user, get_current_user_optional
from app.database.users import UserInDB, DatabaseUsers
from jose import jwt, JWTError
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

def get_department_redirect_url(user: UserInDB) -> str:
    """Get the appropriate redirect URL based on user's department and role"""
    department = getattr(user, 'department', '').lower()
    role = getattr(user, 'role', '').lower()
    
    # IT Department routing
    if department in ['development', 'it']:
        return "/dashboard"  # Will be handled by global IT route
    
    # Sales Department routing
    elif department == 'sales':
        return "/dashboard"  # Will be handled by global Sales route
    
    # HR Department routing
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return "/dashboard"  # Will be handled by global HR route
    
    # Default fallback
    else:
        return "/dashboard"

@router.get("/app/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: UserInDB = Depends(get_current_user_optional)):
    """Serve the login page or redirect based on department"""
    if current_user:
        # User is already logged in, redirect to their department dashboard
        redirect_url = get_department_redirect_url(current_user)
        return RedirectResponse(url=redirect_url)
    
    return templates.TemplateResponse("login.html", {"request": request})

# Global Department Routes - Auto-redirect based on user's department
@router.get("/dashboard", response_class=HTMLResponse)
async def global_dashboard(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global dashboard route - redirects to department-specific dashboard"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/dashboard.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/dashboard.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/dashboard.html", {"request": request})
    
    # Default fallback
    else:
        return templates.TemplateResponse("departments/sales/dashboard.html", {"request": request})

@router.get("/attendance", response_class=HTMLResponse)
async def global_attendance(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global attendance route - redirects to department-specific attendance"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/attendance.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/attendance.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/attendance.html", {"request": request})
    
    # Default fallback
    else:
        return templates.TemplateResponse("departments/sales/attendance.html", {"request": request})

@router.get("/projects", response_class=HTMLResponse)
async def global_projects(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global projects route - available for IT department"""
    department = getattr(current_user, 'department', '').lower()
    
    # Only IT Department has projects
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/projects.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/leads", response_class=HTMLResponse)
async def global_leads(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global leads route - available for Sales department"""
    department = getattr(current_user, 'department', '').lower()
    
    # Only Sales Department has leads
    if department == 'sales':
        return templates.TemplateResponse("departments/sales/leads.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/customer", response_class=HTMLResponse)
async def global_customers(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global customers route - available for Sales department"""
    department = getattr(current_user, 'department', '').lower()
    
    # Only Sales Department has customers
    if department == 'sales':
        return templates.TemplateResponse("departments/sales/customers.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/employees", response_class=HTMLResponse)
async def global_employees(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global employees route - available for HR department"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # Only HR Department has employee management
    if department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/employees.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/payroll", response_class=HTMLResponse)
async def global_payroll(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global payroll route - available for HR department"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # Only HR Department has payroll management
    if department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/payroll.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/recruitment", response_class=HTMLResponse)
async def global_recruitment(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global recruitment route - available for HR department"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # Only HR Department has recruitment management
    if department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/recruitment.html", {"request": request})
    else:
        # Redirect other departments to their dashboard
        return RedirectResponse(url="/dashboard")

@router.get("/daily-reports", response_class=HTMLResponse)
async def global_daily_reports(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global daily reports route - available for IT and Sales departments"""
    department = getattr(current_user, 'department', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/daily-reports.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/daily-reports.html", {"request": request})
    
    # Redirect other departments to their dashboard
    else:
        return RedirectResponse(url="/dashboard")

@router.get("/team", response_class=HTMLResponse)
async def global_team(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global team route - available for IT and Sales departments (managers/TLs only)"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department - Managers and Team Leaders only
    if department in ['development', 'it'] and role in ['manager', 'dev_manager', 'team_lead']:
        return templates.TemplateResponse("departments/development/team.html", {"request": request})
    
    # Sales Department - Managers only
    elif department == 'sales' and role in ['sales_manager', 'manager']:
        return templates.TemplateResponse("departments/sales/team.html", {"request": request})
    
    # Redirect other roles/departments to their dashboard
    else:
        return RedirectResponse(url="/dashboard")

@router.get("/performance", response_class=HTMLResponse)
async def global_performance(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global performance route - available for all departments"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/performance-reviews.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/performance.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/performance-reviews.html", {"request": request})
    
    # Default fallback
    else:
        return templates.TemplateResponse("departments/sales/performance.html", {"request": request})

@router.get("/leave-requests", response_class=HTMLResponse)
async def global_leave_requests(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global leave requests route - available for all departments"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/leave-requests.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/leave-requests.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/leave-requests.html", {"request": request})
    
    # Default fallback
    else:
        return templates.TemplateResponse("departments/sales/leave-requests.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def global_profile(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global profile route - available for all departments"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # IT Department
    if department in ['development', 'it']:
        return templates.TemplateResponse("departments/development/profile.html", {"request": request})
    
    # Sales Department
    elif department == 'sales':
        return templates.TemplateResponse("departments/sales/profile.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/profile.html", {"request": request})
    
    # Default fallback
    else:
        return templates.TemplateResponse("departments/sales/profile.html", {"request": request})

@router.get("/reports", response_class=HTMLResponse)
async def global_reports(request: Request, current_user: UserInDB = Depends(get_current_user)):
    """Global reports route - available for Sales and HR departments"""
    department = getattr(current_user, 'department', '').lower()
    role = getattr(current_user, 'role', '').lower()
    
    # Sales Department
    if department == 'sales':
        return templates.TemplateResponse("departments/sales/reports.html", {"request": request})
    
    # HR Department
    elif department in ['hr', 'management'] and role in ['hr_manager', 'hr_executives', 'hr', 'admin', 'director']:
        return templates.TemplateResponse("departments/hr/reports.html", {"request": request})
    
    # IT Department - Only for managers/TLs
    elif department in ['development', 'it'] and role in ['manager', 'dev_manager', 'team_lead']:
        return templates.TemplateResponse("departments/development/reports.html", {"request": request})
    
    # Redirect other roles/departments to their dashboard
    else:
        return RedirectResponse(url="/dashboard")

@router.get("/app/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Legacy route - redirect to global dashboard"""
    return RedirectResponse(url="/dashboard")

@router.get("/app/attendance", response_class=HTMLResponse)
async def attendance_page(request: Request):
    """Legacy route - redirect to global attendance"""
    return RedirectResponse(url="/attendance")

@router.get("/app/project", response_class=HTMLResponse)
async def project_page(request: Request):
    """Legacy route - redirect to global projects"""
    return RedirectResponse(url="/projects")

@router.get("/app/reports", response_class=HTMLResponse)
async def daily_reports(request: Request):
    """Legacy route - redirect to global daily reports"""
    return RedirectResponse(url="/daily-reports")

@router.get("/app/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    """Legacy route - redirect to global team"""
    return RedirectResponse(url="/team")

@router.get("/app/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Legacy route - serve the general settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/app/leave-requests", response_class=HTMLResponse)
async def leave_requests_page(request: Request):
    """Legacy route - redirect to global leave requests"""
    return RedirectResponse(url="/leave-requests")

@router.get("/app/js/{filename}")
async def serve_js(filename: str):
    """Serve JavaScript files"""
    file_path = web_dir / "js" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"JavaScript file {filename} not found")
    return FileResponse(file_path)

# Legacy Department-Specific Routes (redirects to global routes)
# Sales Department Routes
@router.get("/app/sales/dashboard", response_class=HTMLResponse)
async def sales_dashboard_page(request: Request):
    """Legacy route - redirect to global dashboard"""
    return RedirectResponse(url="/dashboard")

@router.get("/app/sales/attendance", response_class=HTMLResponse)
async def sales_attendance_page(request: Request):
    """Legacy route - redirect to global attendance"""
    return RedirectResponse(url="/attendance")

@router.get("/app/sales/leads", response_class=HTMLResponse)
async def sales_leads_page(request: Request):
    """Legacy route - redirect to global leads"""
    return RedirectResponse(url="/leads")

@router.get("/app/sales/customers", response_class=HTMLResponse)
async def sales_customers_page(request: Request):
    """Legacy route - redirect to global customers"""
    return RedirectResponse(url="/customer")

@router.get("/app/sales/reports", response_class=HTMLResponse)
async def sales_reports_page(request: Request):
    """Legacy route - redirect to global reports"""
    return RedirectResponse(url="/reports")

@router.get("/app/sales/profile", response_class=HTMLResponse)
async def sales_profile_page(request: Request):
    """Legacy route - redirect to global profile"""
    return RedirectResponse(url="/profile")

@router.get("/app/sales/leave-requests", response_class=HTMLResponse)
async def sales_leave_requests_page(request: Request):
    """Legacy route - redirect to global leave-requests"""
    return RedirectResponse(url="/leave-requests")

@router.get("/app/sales/performance", response_class=HTMLResponse)
async def sales_performance_page(request: Request):
    """Legacy route - redirect to global performance"""
    return RedirectResponse(url="/performance")

@router.get("/app/sales/team", response_class=HTMLResponse)
async def sales_team_page(request: Request):
    """Legacy route - redirect to global team"""
    return RedirectResponse(url="/team")

@router.get("/app/sales/daily-reports", response_class=HTMLResponse)
async def sales_daily_reports_page(request: Request):
    """Legacy route - redirect to global daily-reports"""
    return RedirectResponse(url="/daily-reports")

@router.get("/app/sales/penalties", response_class=HTMLResponse)
async def sales_penalties_page(request: Request):
    """Legacy route - serve the sales penalties page"""
    return templates.TemplateResponse("departments/sales/penalties.html", {"request": request})

@router.get("/app/sales/settings", response_class=HTMLResponse)
async def sales_settings_page(request: Request):
    """Legacy route - serve the sales settings page"""
    return templates.TemplateResponse("departments/sales/settings.html", {"request": request})

# HR Department Routes
@router.get("/app/hr/dashboard", response_class=HTMLResponse)
async def hr_dashboard_page(request: Request):
    """Legacy route - redirect to global dashboard"""
    return RedirectResponse(url="/dashboard")

@router.get("/app/hr/attendance", response_class=HTMLResponse)
async def hr_attendance_page(request: Request):
    """Legacy route - redirect to global attendance"""
    return RedirectResponse(url="/attendance")

@router.get("/app/hr/employees", response_class=HTMLResponse)
async def hr_employees_page(request: Request):
    """Legacy route - redirect to global employees"""
    return RedirectResponse(url="/employees")

@router.get("/app/hr/payroll", response_class=HTMLResponse)
async def hr_payroll_main_page(request: Request):
    """Legacy route - redirect to global payroll"""
    return RedirectResponse(url="/payroll")

@router.get("/app/hr/recruitment", response_class=HTMLResponse)
async def hr_recruitment_page(request: Request):
    """Legacy route - redirect to global recruitment"""
    return RedirectResponse(url="/recruitment")

@router.get("/app/hr/leave-requests", response_class=HTMLResponse)
async def hr_leave_requests_page(request: Request):
    """Legacy route - redirect to global leave-requests"""
    return RedirectResponse(url="/leave-requests")

@router.get("/app/hr/performance", response_class=HTMLResponse)
async def hr_performance_page(request: Request):
    """Legacy route - redirect to global performance"""
    return RedirectResponse(url="/performance")

@router.get("/app/hr/reports", response_class=HTMLResponse)
async def hr_reports_page(request: Request):
    """Legacy route - redirect to global reports"""
    return RedirectResponse(url="/reports")

@router.get("/app/hr/settings", response_class=HTMLResponse)
async def hr_settings_page(request: Request):
    """Legacy route - serve the HR settings page"""
    return templates.TemplateResponse("departments/hr/settings.html", {"request": request})

@router.get("/app/hr/profile", response_class=HTMLResponse)
async def hr_profile_page(request: Request):
    """Legacy route - redirect to global profile"""
    return RedirectResponse(url="/profile")

# IT Department Routes  
@router.get("/app/it/dashboard", response_class=HTMLResponse)
async def it_dashboard_page(request: Request):
    """Legacy route - redirect to global dashboard"""
    return RedirectResponse(url="/dashboard")

@router.get("/app/it/attendance", response_class=HTMLResponse)
async def it_attendance_page(request: Request):
    """Legacy route - redirect to global attendance"""
    return RedirectResponse(url="/attendance")

@router.get("/app/it/projects", response_class=HTMLResponse)
async def it_projects_page(request: Request):
    """Legacy route - redirect to global projects"""
    return RedirectResponse(url="/projects")

@router.get("/app/it/daily-reports", response_class=HTMLResponse)
async def it_daily_reports_page(request: Request):
    """Legacy route - redirect to global daily-reports"""
    return RedirectResponse(url="/daily-reports")

@router.get("/app/it/team", response_class=HTMLResponse)
async def it_team_page(request: Request):
    """Legacy route - redirect to global team"""
    return RedirectResponse(url="/team")

@router.get("/app/it/performance", response_class=HTMLResponse)
async def it_performance_page(request: Request):
    """Legacy route - redirect to global performance"""
    return RedirectResponse(url="/performance")

@router.get("/app/it/leave-requests", response_class=HTMLResponse)
async def it_leave_requests_page(request: Request):
    """Legacy route - redirect to global leave-requests"""
    return RedirectResponse(url="/leave-requests")

@router.get("/app/it/profile", response_class=HTMLResponse)
async def it_profile_page(request: Request):
    """Legacy route - redirect to global profile"""
    return RedirectResponse(url="/profile")

@router.get("/app/it/penalties", response_class=HTMLResponse)
async def it_penalties_page(request: Request):
    """Legacy route - serve the IT penalties page"""
    return templates.TemplateResponse("departments/development/penalties.html", {"request": request})

@router.get("/app/it/reports", response_class=HTMLResponse)
async def it_reports_page(request: Request):
    """Legacy route - redirect to global reports"""
    return RedirectResponse(url="/reports")

@router.get("/app/it/settings", response_class=HTMLResponse)
async def it_settings_page(request: Request):
    """Legacy route - serve the IT settings page"""
    return templates.TemplateResponse("departments/development/settings.html", {"request": request})