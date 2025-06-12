from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from bson import ObjectId

from app.database.daily_reports import ReportCreate, ReportUpdate, ReportResponse, DatabaseDailyReports
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/daily-reports",
    tags=["daily_reports"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ReportResponse)
async def create_daily_report(
    report_data: ReportCreate,
    current_user = Depends(get_current_user)
):
    # Set user_id to current user's ID to prevent the ObjectId error
    report_data.user_id = current_user.id
    
    try:
        report = await DatabaseDailyReports.create_report(report_data)
        # Convert ObjectId to string
        report_dict = report.dict(by_alias=True)
        report_dict["_id"] = str(report_dict["_id"])
        report_dict["user_id"] = str(report_dict["user_id"])
        if report_dict.get("project_id"):
            report_dict["project_id"] = str(report_dict["project_id"])
            
        return report_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error creating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.get("/today", response_model=Optional[ReportResponse])
async def get_today_report(current_user = Depends(get_current_user)):
    today = date.today()
    report = await DatabaseDailyReports.get_report_by_date(str(current_user.id), today)
    
    if not report:
        return None
    
    # Convert ObjectId to string
    report_dict = report.dict(by_alias=True)
    report_dict["_id"] = str(report_dict["_id"])
    report_dict["user_id"] = str(report_dict["user_id"])
    if report_dict.get("project_id"):
        report_dict["project_id"] = str(report_dict["project_id"])
        
    return report_dict

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(report_id: str, current_user = Depends(get_current_user)):
    report = await DatabaseDailyReports.get_report_by_id(report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Ensure user has permission to view this report
    if str(report.user_id) != str(current_user.id) and current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report"
        )
    
    # Convert ObjectId to string
    report_dict = report.dict(by_alias=True)
    report_dict["_id"] = str(report_dict["_id"])
    report_dict["user_id"] = str(report_dict["user_id"])
    if report_dict.get("project_id"):
        report_dict["project_id"] = str(report_dict["project_id"])
        
    return report_dict

@router.get("/", response_model=List[ReportResponse])
async def get_user_reports(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    # Default to last 7 days if dates not provided
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()
    
    reports = await DatabaseDailyReports.get_user_reports(str(current_user.id), start_date, end_date)
    
    # Convert ObjectId to string for each report
    response_reports = []
    for report in reports:
        report_dict = report.dict(by_alias=True)
        report_dict["_id"] = str(report_dict["_id"])
        report_dict["user_id"] = str(report_dict["user_id"])
        if report_dict.get("project_id"):
            report_dict["project_id"] = str(report_dict["project_id"])
        response_reports.append(report_dict)
    
    return response_reports

@router.get("/team/today", response_model=List[ReportResponse])
async def get_team_today_reports(current_user = Depends(get_current_user)):
    # Verify user has permission to view team reports
    if current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team reports"
        )
    
    # Get team members
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    # Get today's reports
    today = date.today()
    reports = await DatabaseDailyReports.get_team_reports(team_ids, today)
    
    # Convert ObjectId to string for each report
    response_reports = []
    for report in reports:
        report_dict = report.dict(by_alias=True)
        report_dict["_id"] = str(report_dict["_id"])
        report_dict["user_id"] = str(report_dict["user_id"])
        if report_dict.get("project_id"):
            report_dict["project_id"] = str(report_dict["project_id"])
        response_reports.append(report_dict)
    
    return response_reports

@router.get("/project/{project_id}", response_model=List[ReportResponse])
async def get_project_reports(
    project_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    # Verify user has permission to view project reports
    # First check if user is part of the project
    from app.database.projects import DatabaseProjects
    project = await DatabaseProjects.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    is_project_member = any(
        str(member.user_id) == str(current_user.id) for member in project.members
    )
    
    if not is_project_member and str(project.lead_id) != str(current_user.id) and current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view reports for this project"
        )
    
    # Default to last 7 days if dates not provided
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()
    
    reports = await DatabaseDailyReports.get_project_reports(project_id, start_date, end_date)
    
    # Convert ObjectId to string for each report
    response_reports = []
    for report in reports:
        report_dict = report.dict(by_alias=True)
        report_dict["_id"] = str(report_dict["_id"])
        report_dict["user_id"] = str(report_dict["user_id"])
        if report_dict.get("project_id"):
            report_dict["project_id"] = str(report_dict["project_id"])
        response_reports.append(report_dict)
    
    return response_reports

@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_data: ReportUpdate,
    current_user = Depends(get_current_user)
):
    # Check if report exists
    report = await DatabaseDailyReports.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Verify user can update this report
    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update reports for other users"
        )
    
    updated_report = await DatabaseDailyReports.update_report(report_id, report_data)
    
    # Convert ObjectId to string
    report_dict = updated_report.dict(by_alias=True)
    report_dict["_id"] = str(report_dict["_id"])
    report_dict["user_id"] = str(report_dict["user_id"])
    if report_dict.get("project_id"):
        report_dict["project_id"] = str(report_dict["project_id"])
        
    return report_dict

@router.get("/stats/personal", response_model=dict)
async def get_personal_report_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    # Default to current month if dates not provided
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        end_date = date.today()
    
    stats = await DatabaseDailyReports.get_report_stats(str(current_user.id), start_date, end_date)
    return stats