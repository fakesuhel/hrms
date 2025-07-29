from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional
from datetime import datetime, date, timedelta, timezone

from app.database.projects import (
    DatabaseProjects, ProjectCreate, ProjectUpdate, 
    ProjectResponse, Project, TaskCreate, TaskUpdate, UserSearchResult
)
from app.utils.auth import get_current_user

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now()

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/users/search", response_model=List[UserSearchResult])
async def search_users(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user = Depends(get_current_user)
):
    """
    Search for users by name, username, or email.
    This is useful for assigning tasks to team members.
    """
    try:
        current_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Searching users with query: '{query}'")
        print(f"Current time: {current_time}, User: {current_user.username}")
        
        results = await DatabaseProjects.search_users(query, limit)
        return results
    except Exception as e:
        print(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        current_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Creating project: {project_data.name}")
        print(f"Current time: {current_time}, User: {current_user.username}")
        
        project = await DatabaseProjects.create_project(
            project_data=project_data,
            manager_id=project_data.manager_id if project_data.manager_id else str(current_user.id)
        )
        
        # Convert to response model
        response_dict = {
            "_id": str(project.id),
            "name": project.name,
            "description": project.description,
            "client": project.client,
            "start_date": project.start_date,  # Already a string
            "end_date": project.end_date,      # Already a string
            "status": project.status,
            "manager_id": str(project.manager_id) if project.manager_id else None,
            "team_members": [str(member) for member in project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    "due_date": task.due_date,  # Already a string
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in project.tasks
            ],
            "budget": project.budget,
            "technologies": project.technologies,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    only_managed: bool = Query(False, description="Filter to only projects where user is manager"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        current_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Getting projects for user: {current_user.id}")
        print(f"Current time: {current_time}, User: {current_user.username}")
        
        projects = await DatabaseProjects.get_projects(
            user_id=str(current_user.id),
            only_managed=only_managed,
            user_role=current_user.role,
            user_department=getattr(current_user, 'department', None)
        )
        
        # Convert to response models
        response_list = []
        for project in projects:
            response_dict = {
                "_id": str(project.id),
                "name": project.name,
                "description": project.description,
                "client": project.client,
                "start_date": project.start_date,  # Already a string
                "end_date": project.end_date,      # Already a string
                "status": project.status,
                "manager_id": str(project.manager_id) if project.manager_id else None,
                "team_members": [str(member) for member in project.team_members],
                "tasks": [
                    {
                        "_id": str(task.id),
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                        "due_date": task.due_date,  # Already a string
                        "created_at": task.created_at,
                        "updated_at": task.updated_at
                    } for task in project.tasks
                ],
                "budget": project.budget,
                "technologies": project.technologies,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }
            response_list.append(ProjectResponse(**response_dict))
        
        return response_list
        
    except Exception as e:
        print(f"Error getting projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get projects: {str(e)}"
        )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str = Path(..., description="The ID of the project to retrieve"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        current_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Getting project: {project_id}")
        print(f"Current time: {current_time}, User: {current_user.username}")
        
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Check permissions
        # if str(project.manager_id) != str(current_user.id) and str(current_user.id) not in [str(m) for m in project.team_members]:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="You don't have permission to view this project"
        #     )
        
        # Convert to response model
        response_dict = {
            "_id": str(project.id),
            "name": project.name,
            "description": project.description,
            "client": project.client,
            "start_date": project.start_date,  # Already a string
            "end_date": project.end_date,      # Already a string
            "status": project.status,
            "manager_id": str(project.manager_id) if project.manager_id else None,
            "team_members": [str(member) for member in project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    "due_date": task.due_date,  # Already a string
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in project.tasks
            ],
            "budget": project.budget,
            "technologies": project.technologies,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    update_data: ProjectUpdate,
    project_id: str = Path(..., description="The ID of the project to update"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Updating project: {project_id}")
        print(f"Current time: 2025-06-12 07:37:38, User: soheruNow")
        
        # First, get the project to check permissions
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Only the project manager can update the project
        if project.manager_id and str(project.manager_id) != str(current_user.id):
            # Allow admins and directors to edit any project
            if current_user.role not in ['admin', 'director']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the project manager, admin, or director can update the project"
                )
            
        # Update the project
        updated_project = await DatabaseProjects.update_project(project_id, update_data)
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Convert to response model
        response_dict = {
            "_id": str(updated_project.id),
            "name": updated_project.name,
            "description": updated_project.description,
            "client": updated_project.client,
            # start_date and end_date are already strings, do not call isoformat
            "start_date": updated_project.start_date,
            "end_date": updated_project.end_date,
            "status": updated_project.status,
            "manager_id": str(updated_project.manager_id) if updated_project.manager_id else None,
            "team_members": [str(member) for member in updated_project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    # due_date is already a string, do not call isoformat
                    "due_date": task.due_date,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in updated_project.tasks
            ],
            "budget": updated_project.budget,
            "technologies": updated_project.technologies,
            "created_at": updated_project.created_at,
            "updated_at": updated_project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str = Path(..., description="The ID of the project to delete"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Deleting project: {project_id}")
        print(f"Current time: 2025-06-12 07:37:38, User: soheruNow")
        
        # First, get the project to check permissions
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Only the project manager can delete the project
        if project.manager_id and str(project.manager_id) != str(current_user.id):
            # Allow admins and directors to delete any project
            if current_user.role not in ['admin', 'director']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the project manager, admin, or director can delete the project"
                )
            
        # Delete the project
        success = await DatabaseProjects.delete_project(project_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.post("/{project_id}/tasks", response_model=ProjectResponse)
async def add_task(
    task_data: TaskCreate,
    project_id: str = Path(..., description="The ID of the project to add a task to"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Adding task to project: {project_id}")
        print(f"Task title: {task_data.title}")
        print(f"Current time: 2025-06-12 07:37:38, User: soheruNow")
        
        # First, get the project to check permissions
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Only the project manager or team members can add tasks
        can_add_task = (
            (project.manager_id and str(project.manager_id) == str(current_user.id)) or
            str(current_user.id) in [str(m) for m in project.team_members] or
            current_user.role in ['admin', 'director', 'dev_manager']
        )
        
        if not can_add_task:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add tasks to this project"
            )
            
        # Add the task
        updated_project = await DatabaseProjects.add_task(project_id, task_data)
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Convert to response model
        response_dict = {
            "_id": str(updated_project.id),
            "name": updated_project.name,
            "description": updated_project.description,
            "client": updated_project.client,
            "start_date": updated_project.start_date,
            "end_date": updated_project.end_date,
            "status": updated_project.status,
            "manager_id": str(updated_project.manager_id) if updated_project.manager_id else None,
            "team_members": [str(member) for member in updated_project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    "due_date": task.due_date,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in updated_project.tasks
            ],
            "budget": updated_project.budget,
            "technologies": updated_project.technologies,
            "created_at": updated_project.created_at,
            "updated_at": updated_project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add task: {str(e)}"
        )

@router.put("/{project_id}/tasks/{task_id}", response_model=ProjectResponse)
async def update_task(
    update_data: TaskUpdate,
    project_id: str = Path(..., description="The ID of the project"),
    task_id: str = Path(..., description="The ID of the task to update"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Updating task {task_id} in project: {project_id}")
        print(f"Current time: 2025-06-12 07:37:38, User: soheruNow")
        
        # First, get the project to check permissions
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Only the project manager or team members can update tasks
        can_update_task = (
            (project.manager_id and str(project.manager_id) == str(current_user.id)) or
            str(current_user.id) in [str(m) for m in project.team_members] or
            current_user.role in ['admin', 'director', 'dev_manager']
        )
        
        if not can_update_task:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update tasks in this project"
            )
            
        # Update the task
        updated_project = await DatabaseProjects.update_task(project_id, task_id, update_data)
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project or task not found"
            )
            
        # Convert to response model
        response_dict = {
            "_id": str(updated_project.id),
            "name": updated_project.name,
            "description": updated_project.description,
            "client": updated_project.client,
            "start_date": updated_project.start_date,
            "end_date": updated_project.end_date,
            "status": updated_project.status,
            "manager_id": str(updated_project.manager_id) if updated_project.manager_id else None,
            "team_members": [str(member) for member in updated_project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    "due_date": task.due_date,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in updated_project.tasks
            ],
            "budget": updated_project.budget,
            "technologies": updated_project.technologies,
            "created_at": updated_project.created_at,
            "updated_at": updated_project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.delete("/{project_id}/tasks/{task_id}", response_model=ProjectResponse)
async def delete_task(
    project_id: str = Path(..., description="The ID of the project"),
    task_id: str = Path(..., description="The ID of the task to delete"),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Deleting task {task_id} from project: {project_id}")
        print(f"Current time: 2025-06-12 07:37:38, User: soheruNow")
        
        # First, get the project to check permissions
        project = await DatabaseProjects.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
            
        # Only the project manager or team members can delete tasks
        can_delete_task = (
            (project.manager_id and str(project.manager_id) == str(current_user.id)) or
            str(current_user.id) in [str(m) for m in project.team_members] or
            current_user.role in ['admin', 'director', 'dev_manager']
        )
        
        if not can_delete_task:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete tasks in this project"
            )
            
        # Delete the task
        updated_project = await DatabaseProjects.delete_task(project_id, task_id)
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project or task not found"
            )
            
        # Convert to response model
        response_dict = {
            "_id": str(updated_project.id),
            "name": updated_project.name,
            "description": updated_project.description,
            "client": updated_project.client,
            "start_date": updated_project.start_date,
            "end_date": updated_project.end_date,
            "status": updated_project.status,
            "manager_id": str(updated_project.manager_id) if updated_project.manager_id else None,
            "team_members": [str(member) for member in updated_project.team_members],
            "tasks": [
                {
                    "_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                    "due_date": task.due_date,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                } for task in updated_project.tasks
            ],
            "budget": updated_project.budget,
            "technologies": updated_project.technologies,
            "created_at": updated_project.created_at,
            "updated_at": updated_project.updated_at
        }
        
        return ProjectResponse(**response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )

@router.get("/stats/summary")
async def get_project_stats(current_user = Depends(get_current_user)):
    try:
        # Debug logging
        current_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Getting project stats for user: {current_user.id}")
        print(f"Current time: 2025-06-12 09:35:23, User: {current_user.username}")
        
        # Get the stats from the database
        stats = await DatabaseProjects.get_project_stats(str(current_user.id))
        
        # Add the current user's username from the authentication context
        stats["current_user"] = current_user.username
        
        return stats
        
    except Exception as e:
        print(f"Error getting project stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project stats: {str(e)}"
        )