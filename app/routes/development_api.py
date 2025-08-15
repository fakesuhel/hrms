from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from app.utils.auth import get_current_user
from app.database.users import UserInDB
from app.database.projects import (
    DatabaseProjects, ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate
)
from app.database.teams import DatabaseTeams
from app.database.attendance import DatabaseAttendance
from app.database.daily_reports import DatabaseDailyReports
from datetime import datetime, date, timedelta
from bson import ObjectId

router = APIRouter(prefix="/api/development", tags=["development"])

# Enhanced Project Management
@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new project"""
    if current_user.role not in ["director", "dev_manager", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create projects"
        )
    
    try:
        new_project = await DatabaseProjects.create_project(project_data, str(current_user.id))
        return ProjectResponse(**new_project.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating project: {str(e)}"
        )

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    status: Optional[str] = Query(None, description="Filter by project status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get projects based on user role"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "developer", "intern"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view projects"
        )
    
    try:
        user_id = str(current_user.id)
        
        if current_user.role in ["director", "dev_manager"]:
            # Managers can see all projects
            projects = await DatabaseProjects.get_projects(user_id, only_managed=False)
        elif current_user.role == "team_lead":
            # Team leads can see managed projects and assigned projects
            projects = await DatabaseProjects.get_projects(user_id, only_managed=False)
        else:
            # Developers and interns can only see assigned projects
            projects = await DatabaseProjects.get_projects(user_id, only_managed=False)
            # Filter to only projects where user is a team member
            projects = [p for p in projects if user_id in p.team_members]
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        return [ProjectResponse(**project.model_dump()) for project in projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching projects: {str(e)}"
        )

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a specific project by ID"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "developer", "intern"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view projects"
        )
    
    try:
        project = await DatabaseProjects.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        user_id = str(current_user.id)
        
        # Check if user has access to this project
        if current_user.role in ["developer", "intern"]:
            if user_id not in project.team_members and project.manager_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this project"
                )
        
        return ProjectResponse(**project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching project: {str(e)}"
        )

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a project"""
    if current_user.role not in ["director", "dev_manager", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update projects"
        )
    
    try:
        # Check if project exists and user has permission
        existing_project = await DatabaseProjects.get_project(project_id)
        if not existing_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        user_id = str(current_user.id)
        
        # Team leads can only update projects they manage
        if current_user.role == "team_lead" and existing_project.manager_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this project"
            )
        
        updated_project = await DatabaseProjects.update_project(project_id, update_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update project"
            )
        
        return ProjectResponse(**updated_project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}"
        )

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a project"""
    if current_user.role not in ["director", "dev_manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete projects"
        )
    
    try:
        success = await DatabaseProjects.delete_project(project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting project: {str(e)}"
        )

# Task Management
@router.post("/projects/{project_id}/tasks")
async def add_project_task(
    project_id: str,
    task_data: TaskCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Add a task to a project"""
    if current_user.role not in ["director", "dev_manager", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add tasks"
        )
    
    try:
        # Verify project exists and user has access
        project = await DatabaseProjects.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        user_id = str(current_user.id)
        
        # Team leads can only add tasks to projects they manage
        if current_user.role == "team_lead" and project.manager_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add tasks to this project"
            )
        
        updated_project = await DatabaseProjects.add_task(project_id, task_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add task"
            )
        
        return {"message": "Task added successfully", "project": ProjectResponse(**updated_project.model_dump())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding task: {str(e)}"
        )

@router.put("/projects/{project_id}/tasks/{task_id}")
async def update_project_task(
    project_id: str,
    task_id: str,
    task_data: TaskUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a task in a project"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "developer", "intern"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update tasks"
        )
    
    try:
        # Verify project exists
        project = await DatabaseProjects.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        user_id = str(current_user.id)
        
        # Find the task
        task = None
        for t in project.tasks:
            if str(t.id) == task_id:
                task = t
                break
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions
        if current_user.role in ["developer", "intern"]:
            # Developers can only update tasks assigned to them
            if task.assigned_to != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this task"
                )
        elif current_user.role == "team_lead":
            # Team leads can update tasks in projects they manage
            if project.manager_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update tasks in this project"
                )
        
        updated_project = await DatabaseProjects.update_task(project_id, task_id, task_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update task"
            )
        
        return {"message": "Task updated successfully", "project": ProjectResponse(**updated_project.model_dump())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )

# Team Management for Development
@router.get("/teams")
async def get_development_teams(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get development teams"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "developer", "intern"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view teams"
        )
    
    try:
        # Get teams from development department
        from app.database.teams import teams_collection
        query = {"department": "development"}
        
        user_id = str(current_user.id)
        
        if current_user.role in ["developer", "intern"]:
            # Only show teams where user is a member
            query["members.user_id"] = user_id
        elif current_user.role == "team_lead":
            # Show teams where user is the lead
            query["$or"] = [
                {"lead_id": user_id},
                {"members.user_id": user_id}
            ]
        
        teams = list(teams_collection.find(query))
        
        # Convert ObjectId to string
        for team in teams:
            team["id"] = str(team["_id"])
            del team["_id"]
            team["lead_id"] = str(team["lead_id"])
            
            # Convert member ObjectIds to strings
            for member in team.get("members", []):
                member["user_id"] = str(member["user_id"])
        
        return teams
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching teams: {str(e)}"
        )

@router.get("/team-members")
async def get_team_members(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get team members for project assignment"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team members"
        )
    
    try:
        # Get development department users
        from app.database.users import users_collection
        query = {
            "department": "development",
            "is_active": True
        }
        
        users = list(users_collection.find(query, {
            "_id": 1,
            "username": 1,
            "full_name": 1,
            "role": 1,
            "position": 1
        }))
        
        # Convert to expected format
        team_members = []
        for user in users:
            team_members.append({
                "id": str(user["_id"]),
                "username": user["username"],
                "full_name": user.get("full_name", user["username"]),
                "role": user.get("role", "developer"),
                "position": user.get("position", "Developer")
            })
        
        return team_members
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching team members: {str(e)}"
        )

# Development Analytics and Reports
@router.get("/stats/projects")
async def get_project_stats(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get project statistics"""
    if current_user.role not in ["director", "dev_manager", "team_lead", "developer", "intern"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view project statistics"
        )
    
    try:
        user_id = str(current_user.id)
        
        if current_user.role in ["director", "dev_manager"]:
            # Get all project stats
            stats = await DatabaseProjects.get_project_stats("")
        else:
            # Get user-specific stats
            stats = await DatabaseProjects.get_project_stats(user_id)
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching project stats: {str(e)}"
        )

@router.get("/reports/productivity")
async def get_productivity_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    team_member_id: Optional[str] = Query(None, description="Filter by team member"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get productivity report for development team"""
    if current_user.role not in ["director", "dev_manager", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view productivity reports"
        )
    
    try:
        # Convert string dates to date objects
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get development team members
        from app.database.users import users_collection
        query = {"department": "development", "is_active": True}
        if team_member_id:
            query["_id"] = ObjectId(team_member_id)
        
        team_members = list(users_collection.find(query, {
            "_id": 1, "full_name": 1, "role": 1
        }))
        
        report_data = []
        
        for member in team_members:
            member_id = str(member["_id"])
            
            # Get daily reports for the period
            daily_reports = await DatabaseDailyReports.get_user_reports_by_date_range(
                member_id, start_date_obj, end_date_obj
            )
            
            # Get attendance for the period
            attendance_records = await DatabaseAttendance.get_attendance_by_date_range(
                member_id, start_date_obj, end_date_obj
            )
            
            # Calculate metrics
            total_reports = len(daily_reports)
            total_tasks = sum(len(report.completed_tasks) for report in daily_reports)
            present_days = len([a for a in attendance_records if a.status == "present"])
            
            # Get project assignments
            user_projects = await DatabaseProjects.get_projects(member_id, only_managed=False)
            user_projects = [p for p in user_projects if member_id in p.team_members]
            
            # Calculate task completion rate
            total_assigned_tasks = 0
            completed_tasks = 0
            
            for project in user_projects:
                for task in project.tasks:
                    if task.assigned_to == member_id:
                        total_assigned_tasks += 1
                        if task.status == "completed":
                            completed_tasks += 1
            
            completion_rate = (completed_tasks / total_assigned_tasks * 100) if total_assigned_tasks > 0 else 0
            
            report_data.append({
                "member_id": member_id,
                "member_name": member["full_name"],
                "role": member.get("role", "developer"),
                "daily_reports_submitted": total_reports,
                "total_tasks_reported": total_tasks,
                "present_days": present_days,
                "assigned_projects": len(user_projects),
                "total_assigned_tasks": total_assigned_tasks,
                "completed_tasks": completed_tasks,
                "task_completion_rate": round(completion_rate, 2),
                "average_tasks_per_day": round(total_tasks / present_days, 2) if present_days > 0 else 0
            })
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "team_productivity": report_data,
            "summary": {
                "total_team_members": len(report_data),
                "total_projects": len(set(p.id for member_data in report_data for p in await DatabaseProjects.get_projects(member_data["member_id"], only_managed=False))),
                "average_completion_rate": round(sum(m["task_completion_rate"] for m in report_data) / len(report_data), 2) if report_data else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating productivity report: {str(e)}"
        )

@router.get("/reports/project-status")
async def get_project_status_report(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get project status overview report"""
    if current_user.role not in ["director", "dev_manager", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view project status reports"
        )
    
    try:
        # Get all development projects
        all_projects = await DatabaseProjects.get_projects("", only_managed=False)
        
        # Filter projects if team lead
        if current_user.role == "team_lead":
            user_id = str(current_user.id)
            all_projects = [p for p in all_projects if p.manager_id == user_id or user_id in p.team_members]
        
        # Categorize projects
        status_summary = {
            "planning": [],
            "active": [],
            "on_hold": [],
            "completed": [],
            "cancelled": []
        }
        
        for project in all_projects:
            project_data = {
                "id": str(project.id),
                "name": project.name,
                "client": project.client,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "team_size": len(project.team_members),
                "total_tasks": len(project.tasks),
                "completed_tasks": len([t for t in project.tasks if t.status == "completed"]),
                "in_progress_tasks": len([t for t in project.tasks if t.status == "in_progress"]),
                "progress_percentage": round(
                    (len([t for t in project.tasks if t.status == "completed"]) / len(project.tasks) * 100) 
                    if project.tasks else 0, 2
                )
            }
            
            status_summary[project.status].append(project_data)
        
        return {
            "report_date": datetime.now().isoformat(),
            "total_projects": len(all_projects),
            "projects_by_status": {
                status: {
                    "count": len(projects),
                    "projects": projects
                }
                for status, projects in status_summary.items()
            },
            "overall_stats": {
                "total_tasks": sum(len(p.tasks) for p in all_projects),
                "completed_tasks": sum(len([t for t in p.tasks if t.status == "completed"]) for p in all_projects),
                "in_progress_tasks": sum(len([t for t in p.tasks if t.status == "in_progress"]) for p in all_projects),
                "average_project_progress": round(
                    sum(len([t for t in p.tasks if t.status == "completed"]) / len(p.tasks) * 100 if p.tasks else 0 for p in all_projects) / len(all_projects), 2
                ) if all_projects else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating project status report: {str(e)}"
        )
