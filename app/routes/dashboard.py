from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime, timedelta
from app.database.leave_requests import DatabaseLeaveRequests
from app.database.users import DatabaseUsers
from app.database.attendance import DatabaseAttendance
from app.database.projects import DatabaseProjects
from app.database.daily_reports import DatabaseDailyReports
from app.utils.auth import get_current_user, has_team_access

# Create a router for dashboard endpoints
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/employee-stats", response_model=Dict[str, Any])
async def get_employee_dashboard_stats(current_user = Depends(get_current_user)):
    """
    Get dashboard stats for an employee view
    """
    try:
        # Use the employee dashboard method from DatabaseLeaveRequests
        dashboard_data = await DatabaseLeaveRequests.get_employee_dashboard(str(current_user.id))
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get employee dashboard data: {str(e)}"
        )

@router.get("/team-stats", response_model=Dict[str, Any])
async def get_team_dashboard_stats(
    current_user = Depends(get_current_user),
    team_access = Depends(has_team_access)
):
    """
    Get dashboard stats for a team lead/manager view
    """
    if not team_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access team dashboard"
        )
    
    try:
        # Get team members
        team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
        member_ids = [str(member.id) for member in team_members]
        
        # Get team attendance stats
        attendance_stats = await DatabaseAttendance.get_team_attendance_stats(member_ids)
        
        # Get team projects
        team_projects = await DatabaseProjects.get_team_projects(member_ids)
        
        # Get pending leave requests
        pending_leaves = await DatabaseLeaveRequests.get_pending_approval_requests(str(current_user.id))
        
        # Get team performance average
        # This would normally come from a performance_reviews collection
        team_performance = 4.2  # Placeholder value
        
        # Build and return the team dashboard response
        return {
            "attendance": {
                "team_rate": attendance_stats.get("team_rate", 0),
                "present_count": attendance_stats.get("present_count", 0),
                "team_size": len(member_ids)
            },
            "projects": {
                "team_count": len(team_projects),
                "projects": team_projects[:5]  # First 5 projects
            },
            "performance": {
                "team_average": team_performance
            },
            "leave": {
                "pending_requests": len(pending_leaves),
                "requests": [leave.dict() for leave in pending_leaves[:3]]  # First 3 pending requests
            },
            "team": {
                "size": len(member_ids),
                "members": [member.dict() for member in team_members[:5]]  # First 5 team members
            },
            "recent_activity": {
                "reports": await DatabaseDailyReports.get_team_reports(member_ids, limit=5)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team dashboard data: {str(e)}"
        )
