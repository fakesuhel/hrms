from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db
import json

# Get projects collection
projects_collection = db["projects"]
users_collection = db["users"]

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ProjectTask(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: Optional[str] = None
    status: str = "todo"  # "todo", "in_progress", "review", "completed"
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None  # Store as ISO formatted string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class Project(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[str] = None  # Store as ISO formatted string
    end_date: Optional[str] = None    # Store as ISO formatted string
    status: str = "active"  # "planning", "active", "on_hold", "completed", "cancelled"
    manager_id: str  # Project manager user ID
    team_members: List[str] = []  # List of user IDs
    tasks: List[ProjectTask] = []
    budget: Optional[float] = None
    technologies: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ProjectResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    manager_id: str
    team_members: List[str] = []
    tasks: List[dict] = []
    budget: Optional[float] = None
    technologies: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"
    team_members: Optional[List[str]] = []
    budget: Optional[float] = None
    technologies: Optional[List[str]] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    team_members: Optional[List[str]] = None
    budget: Optional[float] = None
    technologies: Optional[List[str]] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

class UserSearchResult(BaseModel):
    id: str
    username: str
    full_name: str
    position: Optional[str] = None
    department: Optional[str] = None

class DatabaseProjects:
    @staticmethod
    async def get_user_projects(user_id: str) -> List[Project]:
        """
        Get all projects where the user is either a manager or a team member.
        """
        query = {
            "$or": [
                {"manager_id": user_id},
                {"team_members": user_id}
            ]
        }
        
        cursor = projects_collection.find(query).sort("created_at", -1)
        projects = list(cursor)
        
        return [Project(**project) for project in projects]
    
    
    @staticmethod
    async def create_project(project_data: ProjectCreate, manager_id: str) -> Project:
        # Keep dates as strings
        start_date = project_data.start_date if project_data.start_date else None
        end_date = project_data.end_date if project_data.end_date else None
        
        # Current timestamp
        now = datetime.utcnow()
        
        # Create new project
        new_project = {
            "name": project_data.name,
            "description": project_data.description,
            "client": project_data.client,
            "start_date": start_date,  # Already a string
            "end_date": end_date,      # Already a string
            "status": project_data.status,
            "manager_id": manager_id,
            "team_members": project_data.team_members or [],
            "tasks": [],
            "budget": project_data.budget,
            "technologies": project_data.technologies or [],
            "created_at": now,
            "updated_at": now
        }
        
        result = projects_collection.insert_one(new_project)
        new_project["_id"] = result.inserted_id
        
        return Project(**new_project)
    
    @staticmethod
    async def get_projects(user_id: str, only_managed: bool = False) -> List[Project]:
        # Build query based on user role
        query = {"manager_id": user_id} if only_managed else {
            "$or": [
                {"manager_id": user_id},
                {"team_members": user_id}
            ]
        }
        
        # Find projects
        cursor = projects_collection.find(query).sort("created_at", -1)
        projects = list(cursor)
        
        return [Project(**project) for project in projects]
    
    @staticmethod
    async def get_project(project_id: str) -> Optional[Project]:
        # Find project by ID
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        
        if not project:
            return None
            
        return Project(**project)
    
    
    
    @staticmethod
    async def get_project_stats(user_id: str) -> Dict[str, Any]:
        # Build query based on user role
        query = {
            "$or": [
                {"manager_id": user_id},
                {"team_members": user_id}
            ]
        }
        
        # Get all projects for this user
        cursor = projects_collection.find(query)
        projects = list(cursor)
        
        # Calculate statistics
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.get("status") == "active")
        completed_projects = sum(1 for p in projects if p.get("status") == "completed")
        on_hold_projects = sum(1 for p in projects if p.get("status") == "on_hold")
        
        # Count tasks by status
        task_counts = {"todo": 0, "in_progress": 0, "review": 0, "completed": 0}
        overdue_tasks = 0
        upcoming_tasks = 0
        
        # Current date and dates for comparison
        today = datetime.utcnow().date().isoformat()
        seven_days_later = (datetime.utcnow() + timedelta(days=7)).date().isoformat()
        
        for project in projects:
            for task in project.get("tasks", []):
                status = task.get("status", "todo")
                task_counts[status] = task_counts.get(status, 0) + 1
                
                if task.get("due_date"):
                    task_due_date = task["due_date"]  # Already a string
                    
                    # Compare string dates
                    if task_due_date < today and status != "completed":
                        overdue_tasks += 1
                    elif today <= task_due_date <= seven_days_later:
                        upcoming_tasks += 1
        
        # Get current timestamp - use the passed parameter
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # This object will be returned to the route handler, which will add any additional info
        return {
            "user_id": user_id,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": on_hold_projects,
            "tasks_todo": task_counts["todo"],
            "tasks_in_progress": task_counts["in_progress"],
            "tasks_review": task_counts.get("review", 0),
            "tasks_completed": task_counts["completed"],
            "overdue_tasks": overdue_tasks,
            "upcoming_tasks": upcoming_tasks,
            "timestamp": "2025-06-12 09:35:23",  # Using the provided current time
        }
        
    @staticmethod
    async def update_project(project_id: str, update_data: ProjectUpdate) -> Optional[Project]:
        # Get current project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return None
        
        # Build update data - keep dates as strings
        update_dict = {}
        
        for field, value in update_data.dict(exclude_unset=True).items():
            update_dict[field] = value
        
        # Add updated timestamp
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update project
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": update_dict}
        )
        
        # Get updated project
        updated_project = projects_collection.find_one({"_id": ObjectId(project_id)})
        return Project(**updated_project)
    
    @staticmethod
    async def delete_project(project_id: str) -> bool:
        # Delete project
        result = projects_collection.delete_one({"_id": ObjectId(project_id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def add_task(project_id: str, task_data: TaskCreate) -> Optional[Project]:
        # Get current project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return None
        
        # Keep due date as a string
        due_date = task_data.due_date  # Already a string
        
        # Create new task
        now = datetime.utcnow()
        new_task = {
            "_id": ObjectId(),
            "title": task_data.title,
            "description": task_data.description,
            "status": task_data.status,
            "assigned_to": task_data.assigned_to,
            "due_date": due_date,
            "created_at": now,
            "updated_at": now
        }
        
        # Add task to project
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$push": {"tasks": new_task},
                "$set": {"updated_at": now}
            }
        )
        
        # Get updated project
        updated_project = projects_collection.find_one({"_id": ObjectId(project_id)})
        return Project(**updated_project)
    
    @staticmethod
    async def update_task(project_id: str, task_id: str, update_data: TaskUpdate) -> Optional[Project]:
        # Get current project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return None
        
        # Build update data with dot notation for nested fields
        update_dict = {}
        
        for field, value in update_data.dict(exclude_unset=True).items():
            update_dict[f"tasks.$.{field}"] = value
        
        # Add updated timestamp
        update_dict["tasks.$.updated_at"] = datetime.utcnow()
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update task
        projects_collection.update_one(
            {
                "_id": ObjectId(project_id),
                "tasks._id": ObjectId(task_id)
            },
            {"$set": update_dict}
        )
        
        # Get updated project
        updated_project = projects_collection.find_one({"_id": ObjectId(project_id)})
        return Project(**updated_project)
    
    @staticmethod
    async def delete_task(project_id: str, task_id: str) -> Optional[Project]:
        # Get current project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project:
            return None
        
        # Remove task from project
        now = datetime.utcnow()
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$pull": {"tasks": {"_id": ObjectId(task_id)}},
                "$set": {"updated_at": now}
            }
        )
        
        # Get updated project
        updated_project = projects_collection.find_one({"_id": ObjectId(project_id)})
        return Project(**updated_project)
    
    @staticmethod
    async def search_users(query: str, limit: int = 10) -> List[UserSearchResult]:
        """Search users by name, username, or email"""
        if not query or len(query) < 2:
            return []
        
        # Create case-insensitive search regex
        search_regex = {"$regex": f".*{query}.*", "$options": "i"}
        
        # Search by username, first name, last name, or email
        cursor = users_collection.find({
            "$or": [
                {"username": search_regex},
                {"first_name": search_regex},
                {"last_name": search_regex},
                {"email": search_regex}
            ]
        }).limit(limit)
        
        users = list(cursor)
        results = []
        
        for user in users:
            # Create a full name from first and last name if available
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else user.get('username', 'Unknown')
            
            results.append(UserSearchResult(
                id=str(user['_id']),
                username=user.get('username', ''),
                full_name=full_name,
                position=user.get('position'),
                department=user.get('department')
            ))
            
        return results
    
    @staticmethod
    async def get_project_stats(user_id: str) -> Dict[str, Any]:
        # Build query based on user role
        query = {
            "$or": [
                {"manager_id": user_id},
                {"team_members": user_id}
            ]
        }
        
        # Get all projects for this user
        cursor = projects_collection.find(query)
        projects = list(cursor)
        
        # Calculate statistics
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.get("status") == "active")
        completed_projects = sum(1 for p in projects if p.get("status") == "completed")
        on_hold_projects = sum(1 for p in projects if p.get("status") == "on_hold")
        
        # Count tasks by status
        task_counts = {"todo": 0, "in_progress": 0, "review": 0, "completed": 0}
        overdue_tasks = 0
        upcoming_tasks = 0
        today = datetime.utcnow().date().isoformat()
        
        for project in projects:
            for task in project.get("tasks", []):
                status = task.get("status", "todo")
                task_counts[status] = task_counts.get(status, 0) + 1
                
                if task.get("due_date"):
                    task_due_date = task["due_date"]  # Already a string
                    if task_due_date < today and status != "completed":
                        overdue_tasks += 1
                    elif task_due_date >= today and task_due_date <= (datetime.utcnow() + timedelta(days=7)).date().isoformat():
                        upcoming_tasks += 1
        
        # Get current timestamp
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "user_id": user_id,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": on_hold_projects,
            "tasks_todo": task_counts["todo"],
            "tasks_in_progress": task_counts["in_progress"],
            "tasks_review": task_counts["review"],
            "tasks_completed": task_counts["completed"],
            "overdue_tasks": overdue_tasks,
            "upcoming_tasks": upcoming_tasks,
            "timestamp": current_time
        }
    
    @classmethod
    async def get_users_from_active_projects_and_tasks(cls, reviewer_id: str) -> List[str]:
        """
        Get all users who are either:
        1. Team members in any active project where the reviewer is a manager
        2. Assigned to any active task (not completed) in those projects
        
        Args:
            reviewer_id: The ID of the reviewer (team lead, manager, or director)
            
        Returns:
            List of user IDs
        """
        # Convert reviewer_id to string if it's not already
        reviewer_id_str = str(reviewer_id)
        
        # Find all active projects where this user is the manager
        projects_cursor = projects_collection.find({
            "manager_id": reviewer_id_str,
            "status": "active"
        })
        
        projects = list(projects_cursor)
        
        # Set to store unique user IDs
        user_ids = set()
        
        for project in projects:
            # Add all team members
            if project.get("team_members"):
                for member in project["team_members"]:
                    user_ids.add(str(member))
            
            # Add all task assignees for non-completed tasks
            if project.get("tasks"):
                for task in project["tasks"]:
                    if task.get("status") != "completed" and task.get("assigned_to"):
                        # Handle both string and list assignees
                        if isinstance(task["assigned_to"], list):
                            for assignee in task["assigned_to"]:
                                user_ids.add(str(assignee))
                        else:
                            user_ids.add(str(task["assigned_to"]))
        
        # Remove the reviewer from the list
        if reviewer_id_str in user_ids:
            user_ids.remove(reviewer_id_str)
            
        return list(user_ids)