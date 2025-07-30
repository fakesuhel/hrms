from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from typing import List, Optional
from app.utils.auth import get_current_user
from app.database.users import UserInDB, DatabaseUsers, UserCreate
from app.database.recruitment import (
    DatabaseJobPostings, DatabaseJobApplications, DatabaseInterviews,
    JobPostingCreate, JobPostingUpdate, JobPostingInDB,
    JobApplicationCreate, JobApplicationUpdate, JobApplicationInDB,
    InterviewCreate, InterviewUpdate, InterviewInDB
)
from app.database.hr_policies import (
    DatabaseHRPolicies, DatabasePolicyAcknowledgments,
    HRPolicyCreate, HRPolicyUpdate, HRPolicyInDB,
    PolicyAcknowledgmentCreate
)
from app.database.attendance import DatabaseAttendance
from app.database.leave_requests import DatabaseLeaveRequests
from app.database.performance_reviews import DatabasePerformanceReviews
from datetime import datetime, date
import os
import uuid

router = APIRouter(prefix="/api/hr", tags=["hr"])

# Dashboard Endpoints
@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: UserInDB = Depends(get_current_user)):
    """Get HR dashboard statistics"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view HR dashboard stats"
        )
    
    try:
        from app.database.users import users_collection
        from app.database.attendance import attendance_collection
        from app.database.recruitment import job_postings_collection
        
        # Total employees
        total_employees = users_collection.count_documents({"is_active": True})
        
        # Today's attendance rate
        today = datetime.now().date()
        today_attendance = attendance_collection.count_documents({
            "date": today.isoformat(),
            "check_in": {"$exists": True}
        })
        attendance_rate = (today_attendance / total_employees * 100) if total_employees > 0 else 0
        
        # Monthly payroll (placeholder - would need payroll collection)
        monthly_payroll = 0  # This would be calculated from actual payroll data
        
        # Open positions
        open_positions = job_postings_collection.count_documents({"status": "active"})
        
        return {
            "total_employees": total_employees,
            "attendance_rate": attendance_rate,
            "monthly_payroll": monthly_payroll,
            "open_positions": open_positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/attendance/today")
async def get_today_attendance(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get today's attendance records"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attendance data"
        )
    
    try:
        from app.database.attendance import attendance_collection
        from app.database.users import users_collection
        
        target_date = date if date else datetime.now().date().isoformat()
        
        # Get attendance records for the date
        attendance_records = list(attendance_collection.find({"date": target_date}))
        
        # Enrich with user data
        enriched_records = []
        for record in attendance_records:
            user = users_collection.find_one({"_id": record.get("user_id")})
            if user:
                enriched_records.append({
                    **record,
                    "employee_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "department": user.get("department", "N/A"),
                    "is_late": record.get("is_late", False),
                    "status": "present" if record.get("check_in") else "absent"
                })
        
        return enriched_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's attendance: {str(e)}")

@router.delete("/attendance/{attendance_id}")
async def delete_attendance_record(
    attendance_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete an attendance record"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete attendance records"
        )
    
    try:
        success = await DatabaseAttendance.delete_attendance(attendance_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        return {"message": "Attendance record deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting attendance record: {str(e)}"
        )

@router.get("/activities/recent")
async def get_recent_activities(current_user: UserInDB = Depends(get_current_user)):
    """Get recent HR activities"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view HR activities"
        )
    
    try:
        # This would be populated from various activity logs
        # For now, return sample data
        activities = [
            {
                "title": "New Employee Onboarding",
                "description": "John Doe joined the Development team",
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": "Leave Request Approved",
                "description": "Annual leave approved for Jane Smith",
                "timestamp": datetime.now().isoformat()
            }
        ]
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activities: {str(e)}")

@router.get("/pending-actions")
async def get_pending_actions(current_user: UserInDB = Depends(get_current_user)):
    """Get pending HR actions"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view pending actions"
        )
    
    try:
        from app.database.leave_requests import leave_requests_collection
        from app.database.recruitment import applications_collection
        
        pending_actions = []
        
        # Pending leave requests
        pending_leaves = leave_requests_collection.count_documents({"status": "pending"})
        if pending_leaves > 0:
            pending_actions.append({
                "title": "Leave Requests",
                "count": pending_leaves,
                "type": "leave_requests",
                "url": "/web/departments/hr/leave-requests"
            })
        
        # Pending job applications
        pending_applications = applications_collection.count_documents({"status": "applied"})
        if pending_applications > 0:
            pending_actions.append({
                "title": "Job Applications",
                "count": pending_applications,
                "type": "applications",
                "url": "/web/departments/hr/recruitment"
            })
        
        return pending_actions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending actions: {str(e)}")

# Employee Management
@router.get("/employees", response_model=List[dict])
async def get_all_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by employee status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all employees (HR only)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all employees"
        )
    
    try:
        # Get all users from database
        from app.database.users import users_collection
        query = {}
        
        if department:
            query["department"] = department
        if status:
            query["is_active"] = (status == "active")
        
        employees = list(users_collection.find(query, {
            "hashed_password": 0  # Exclude password hash
        }))
        
        # Convert ObjectId to string and format response
        for emp in employees:
            emp["id"] = str(emp["_id"])
            del emp["_id"]
        
        return employees
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees: {str(e)}"
        )

@router.post("/employees")
async def create_employee(
    employee_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new employee"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create employees"
        )
    
    try:
        from app.database.users import UserCreate
        
        # Convert dict to UserCreate model
        # Generate a default password if not provided
        if "password" not in employee_data:
            employee_data["password"] = "TempPass123!"
        
        # Generate username if not provided (use email prefix or name)
        if "username" not in employee_data:
            if "email" in employee_data:
                # Use email prefix as username
                username = employee_data["email"].split("@")[0]
            else:
                # Use first_name + last_name as username
                first_name = employee_data.get("first_name", "")
                last_name = employee_data.get("last_name", "")
                username = f"{first_name.lower()}{last_name.lower()}"
            
            # Ensure username is unique by checking database
            from app.database.users import users_collection
            counter = 1
            original_username = username
            while users_collection.find_one({"username": username}):
                username = f"{original_username}{counter}"
                counter += 1
            
            employee_data["username"] = username
        
        user_create = UserCreate(**employee_data)
        new_employee = await DatabaseUsers.create_user(user_create)
        
        # Remove sensitive information
        employee_dict = new_employee.model_dump()
        employee_dict.pop("hashed_password", None)
        employee_dict["id"] = str(employee_dict.pop("_id", employee_dict.get("id")))
        
        return employee_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employee: {str(e)}"
        )

@router.get("/employees/{employee_id}")
async def get_employee_by_id(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get employee details by ID"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view employee details"
        )
    
    try:
        employee = await DatabaseUsers.get_user_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Remove sensitive information
        employee_dict = employee.model_dump()
        employee_dict.pop("hashed_password", None)
        employee_dict["id"] = str(employee_dict.pop("_id", employee_dict.get("id")))
        
        return employee_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employee: {str(e)}"
        )

@router.put("/employees/{employee_id}")
async def update_employee(
    employee_id: str,
    update_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update employee information"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update employee information"
        )
    
    try:
        from app.database.users import UserUpdate
        
        # Convert dict to UserUpdate model
        user_update = UserUpdate(**update_data)
        updated_employee = await DatabaseUsers.update_user(employee_id, user_update)
        
        if not updated_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Remove sensitive information
        employee_dict = updated_employee.model_dump()
        employee_dict.pop("hashed_password", None)
        employee_dict["id"] = str(employee_dict.pop("_id", employee_dict.get("id")))
        
        return employee_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating employee: {str(e)}"
        )

@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete an employee"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete employees"
        )
    
    try:
        from app.database.users import users_collection
        from bson import ObjectId
        
        # Check if employee exists
        if ObjectId.is_valid(employee_id):
            id_obj = ObjectId(employee_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid employee ID format"
            )
        
        employee = users_collection.find_one({"_id": id_obj})
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Delete employee (soft delete by setting is_active to False)
        result = users_collection.update_one(
            {"_id": id_obj},
            {"$set": {"is_active": False, "deleted_at": datetime.now()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete employee"
            )
        
        return {"message": "Employee deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employee: {str(e)}"
        )

# Recruitment Management

# Job Postings
@router.post("/recruitment/jobs", response_model=dict)
async def create_job_posting(
    job_data: JobPostingCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new job posting"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create job postings"
        )
    
    try:
        new_job = await DatabaseJobPostings.create_job_posting(job_data)
        job_dict = new_job.model_dump()
        job_dict["id"] = str(job_dict.pop("_id"))
        return job_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating job posting: {str(e)}"
        )

@router.get("/recruitment/jobs", response_model=List[dict])
async def get_job_postings(
    status: Optional[str] = Query(None, description="Filter by job status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all job postings"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view job postings"
        )
    
    try:
        jobs = await DatabaseJobPostings.get_all_job_postings(status)
        job_list = []
        for job in jobs:
            job_dict = job.model_dump()
            job_dict["id"] = str(job_dict.pop("_id"))
            job_list.append(job_dict)
        return job_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching job postings: {str(e)}"
        )

@router.get("/recruitment/jobs/{job_id}", response_model=dict)
async def get_job_posting_by_id(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a specific job posting"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view job postings"
        )
    
    try:
        job = await DatabaseJobPostings.get_job_posting_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        job_dict = job.model_dump()
        job_dict["id"] = str(job_dict.pop("_id"))
        return job_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching job posting: {str(e)}"
        )

@router.put("/recruitment/jobs/{job_id}", response_model=dict)
async def update_job_posting(
    job_id: str,
    update_data: JobPostingUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a job posting"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update job postings"
        )
    
    try:
        updated_job = await DatabaseJobPostings.update_job_posting(job_id, update_data)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        job_dict = updated_job.model_dump()
        job_dict["id"] = str(job_dict.pop("_id"))
        return job_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job posting: {str(e)}"
        )

# Job Applications
@router.get("/recruitment/jobs/{job_id}/applications", response_model=List[dict])
async def get_job_applications(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all applications for a job posting"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view job applications"
        )
    
    try:
        applications = await DatabaseJobApplications.get_applications_by_job(job_id)
        app_list = []
        for app in applications:
            app_dict = app.model_dump()
            app_dict["id"] = str(app_dict.pop("_id"))
            app_list.append(app_dict)
        return app_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching applications: {str(e)}"
        )

@router.put("/recruitment/applications/{application_id}", response_model=dict)
async def update_job_application(
    application_id: str,
    update_data: JobApplicationUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update a job application (review, rate, etc.)"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update job applications"
        )
    
    try:
        # Add reviewer information
        update_dict = update_data.model_dump()
        update_dict["reviewer_id"] = str(current_user.id)
        
        updated_app = await DatabaseJobApplications.update_application(
            application_id, JobApplicationUpdate(**update_dict)
        )
        if not updated_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        app_dict = updated_app.model_dump()
        app_dict["id"] = str(app_dict.pop("_id"))
        return app_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating application: {str(e)}"
        )

# Interview Management
@router.post("/recruitment/interviews", response_model=dict)
async def schedule_interview(
    interview_data: InterviewCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Schedule an interview"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to schedule interviews"
        )
    
    try:
        new_interview = await DatabaseInterviews.schedule_interview(interview_data)
        interview_dict = new_interview.model_dump()
        interview_dict["id"] = str(interview_dict.pop("_id"))
        return interview_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error scheduling interview: {str(e)}"
        )

@router.get("/recruitment/interviews/upcoming", response_model=List[dict])
async def get_upcoming_interviews(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get upcoming interviews"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view interviews"
        )
    
    try:
        interviews = await DatabaseInterviews.get_upcoming_interviews()
        interview_list = []
        for interview in interviews:
            interview_dict = interview.model_dump()
            interview_dict["id"] = str(interview_dict.pop("_id"))
            interview_list.append(interview_dict)
        return interview_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching interviews: {str(e)}"
        )

@router.put("/recruitment/interviews/{interview_id}", response_model=dict)
async def update_interview(
    interview_id: str,
    update_data: InterviewUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update an interview"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update interviews"
        )
    
    try:
        updated_interview = await DatabaseInterviews.update_interview(interview_id, update_data)
        if not updated_interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        interview_dict = updated_interview.model_dump()
        interview_dict["id"] = str(interview_dict.pop("_id"))
        return interview_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating interview: {str(e)}"
        )

# HR Policies Management
@router.post("/policies", response_model=dict)
async def create_hr_policy(
    policy_data: HRPolicyCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new HR policy"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create HR policies"
        )
    
    try:
        new_policy = await DatabaseHRPolicies.create_policy(policy_data)
        policy_dict = new_policy.model_dump()
        policy_dict["id"] = str(policy_dict.pop("_id"))
        return policy_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating policy: {str(e)}"
        )

@router.get("/policies", response_model=List[dict])
async def get_hr_policies(
    category: Optional[str] = Query(None, description="Filter by policy category"),
    status: Optional[str] = Query(None, description="Filter by policy status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get HR policies"""
    try:
        if category:
            policies = await DatabaseHRPolicies.get_policies_by_category(category, status)
        else:
            user_department = current_user.department if current_user.role not in ["director", "hr"] else None
            policies = await DatabaseHRPolicies.get_all_policies(status, user_department)
        
        policy_list = []
        for policy in policies:
            policy_dict = policy.model_dump()
            policy_dict["id"] = str(policy_dict.pop("_id"))
            policy_list.append(policy_dict)
        return policy_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching policies: {str(e)}"
        )

@router.get("/policies/{policy_id}", response_model=dict)
async def get_hr_policy_by_id(
    policy_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get a specific HR policy"""
    try:
        policy = await DatabaseHRPolicies.get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        policy_dict = policy.model_dump()
        policy_dict["id"] = str(policy_dict.pop("_id"))
        return policy_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching policy: {str(e)}"
        )

@router.put("/policies/{policy_id}", response_model=dict)
async def update_hr_policy(
    policy_id: str,
    update_data: HRPolicyUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update an HR policy"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update HR policies"
        )
    
    try:
        updated_policy = await DatabaseHRPolicies.update_policy(policy_id, update_data)
        if not updated_policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        policy_dict = updated_policy.model_dump()
        policy_dict["id"] = str(policy_dict.pop("_id"))
        return policy_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating policy: {str(e)}"
        )

@router.post("/policies/{policy_id}/acknowledge")
async def acknowledge_policy(
    policy_id: str,
    acknowledgment_data: PolicyAcknowledgmentCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Acknowledge a policy"""
    try:
        # Get policy to get version
        policy = await DatabaseHRPolicies.get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        acknowledgment = await DatabasePolicyAcknowledgments.acknowledge_policy(
            policy_id, str(current_user.id), acknowledgment_data, policy.version
        )
        
        ack_dict = acknowledgment.model_dump()
        ack_dict["id"] = str(ack_dict.pop("_id"))
        return ack_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error acknowledging policy: {str(e)}"
        )

@router.get("/policies/pending")
async def get_pending_policy_acknowledgments(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get policies that user hasn't acknowledged yet"""
    try:
        pending_policies = await DatabasePolicyAcknowledgments.get_pending_acknowledgments_for_user(
            str(current_user.id), current_user.department or "general"
        )
        
        policy_list = []
        for policy in pending_policies:
            policy_dict = policy.model_dump()
            policy_dict["id"] = str(policy_dict.pop("_id"))
            policy_list.append(policy_dict)
        return policy_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pending acknowledgments: {str(e)}"
        )

# HR Reports and Analytics
@router.get("/reports/attendance")
async def get_attendance_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get attendance report"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attendance reports"
        )
    
    try:
        # Convert string dates to date objects
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get all employees
        from app.database.users import users_collection
        query = {"is_active": True}
        if department:
            query["department"] = department
        
        employees = list(users_collection.find(query, {"_id": 1, "full_name": 1, "department": 1}))
        
        # Get attendance data for each employee
        report_data = []
        for emp in employees:
            emp_id = str(emp["_id"])
            attendance_records = await DatabaseAttendance.get_attendance_by_date_range(
                emp_id, start_date_obj, end_date_obj
            )
            
            present_days = len([a for a in attendance_records if a.status == "present"])
            absent_days = len([a for a in attendance_records if a.status == "absent"])
            late_days = len([a for a in attendance_records if a.is_late])
            
            report_data.append({
                "employee_id": emp_id,
                "employee_name": emp["full_name"],
                "department": emp.get("department", ""),
                "present_days": present_days,
                "absent_days": absent_days,
                "late_days": late_days,
                "total_working_days": len(attendance_records)
            })
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "department": department,
            "employees": report_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating attendance report: {str(e)}"
        )

@router.get("/reports/leave-summary")
async def get_leave_summary_report(
    year: int = Query(..., description="Year for the report"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get leave summary report"""
    if current_user.role not in ["director", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view leave reports"
        )
    
    try:
        # Get all employees
        from app.database.users import users_collection
        query = {"is_active": True}
        if department:
            query["department"] = department
        
        employees = list(users_collection.find(query, {"_id": 1, "full_name": 1, "department": 1}))
        
        # Get leave data for each employee
        report_data = []
        for emp in employees:
            emp_id = str(emp["_id"])
            
            # Get leave requests for the year
            leave_requests = await DatabaseLeaveRequests.get_user_leave_requests(emp_id)
            year_leaves = [
                lr for lr in leave_requests 
                if lr.start_date.year == year or lr.end_date.year == year
            ]
            
            approved_leaves = [lr for lr in year_leaves if lr.status == "approved"]
            total_leave_days = sum(lr.duration_days for lr in approved_leaves)
            
            # Categorize by leave type
            leave_types = {}
            for lr in approved_leaves:
                leave_types[lr.leave_type] = leave_types.get(lr.leave_type, 0) + lr.duration_days
            
            report_data.append({
                "employee_id": emp_id,
                "employee_name": emp["full_name"],
                "department": emp.get("department", ""),
                "total_leave_days": total_leave_days,
                "leave_types": leave_types,
                "pending_requests": len([lr for lr in year_leaves if lr.status == "pending"])
            })
        
        return {
            "year": year,
            "department": department,
            "employees": report_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating leave report: {str(e)}"
        )

# Import database collections at module level for better error handling
try:
    from app.database.users import users_collection
    from app.database.salary_slips import salary_slips_collection
    from app.database.attendance import attendance_collection
except ImportError as e:
    print(f"Warning: Database import error in hr_api.py: {e}")

# Payroll Management Endpoints
@router.get("/payroll")
async def get_payroll_data(
    month: Optional[str] = Query(None, description="Month (01-12)"),
    year: Optional[int] = Query(None, description="Year"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get payroll data for specified month/year"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view payroll data"
        )
    
    try:
        current_date = datetime.now()
        target_month = month or f"{current_date.month:02d}"
        target_year = year or current_date.year
        
        # Debug logging
        print(f"Searching for payroll data: month={target_month}, year={target_year}, department={department}")
        
        # Check if payroll exists for this month/year
        payroll_query = {
            "month": target_month,
            "year": int(target_year)  # Ensure year is integer
        }
        if department:
            payroll_query["department"] = department
        
        print(f"Payroll query: {payroll_query}")
        
        # Check database connection and collection
        try:
            payroll_records = list(salary_slips_collection.find(payroll_query))
            print(f"Found {len(payroll_records)} payroll records")
        except Exception as db_error:
            print(f"Database query error: {db_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database connection error: {str(db_error)}"
            )
        
        if payroll_records:
            # Return existing payroll data
            for record in payroll_records:
                record["id"] = str(record.pop("_id"))
            return payroll_records
        else:
            # Return 404 if no payroll data exists - this is expected behavior
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No payroll data found for {target_month}/{target_year}" + 
                       (f" in department {department}" if department else "")
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in get_payroll_data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payroll data: {str(e)}"
        )

@router.post("/payroll/generate")
async def generate_payroll(
    payroll_request: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate payroll for specified month/year"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate payroll"
        )
    
    try:
        month = payroll_request.get("month")
        year = payroll_request.get("year")
        department = payroll_request.get("department")
        include_bonuses = payroll_request.get("include_bonuses", True)
        include_overtime = payroll_request.get("include_overtime", True)
        
        if not month or not year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month and year are required"
            )
        
        # Get all active employees
        employee_query = {"is_active": True}
        if department:
            employee_query["department"] = department
        
        employees = list(users_collection.find(employee_query))
        
        payroll_records = []
        for employee in employees:
            emp_id = str(employee["_id"])
            base_salary = employee.get("salary", 0)
            
            # Calculate allowances
            hra = base_salary * 0.20  # 20% HRA
            medical_allowance = 1500
            transport_allowance = 1200
            overtime_amount = 0
            bonus_amount = 0
            
            if include_overtime:
                # Calculate overtime from attendance (placeholder)
                overtime_hours = 0  # This would be calculated from attendance data
                overtime_amount = overtime_hours * (base_salary / (22 * 8)) * 1.5  # 1.5x hourly rate
            
            if include_bonuses:
                # Calculate performance bonus (placeholder)
                bonus_amount = 0  # This would be calculated from performance data
            
            total_allowances = hra + medical_allowance + transport_allowance + overtime_amount + bonus_amount
            
            # Calculate deductions
            pf = base_salary * 0.12  # 12% PF
            esi = base_salary * 0.0075  # 0.75% ESI
            income_tax = base_salary * 0.10 if base_salary > 50000 else 0  # 10% tax if salary > 50k
            professional_tax = 200
            late_penalty = 0  # This would be calculated from attendance data
            
            total_deductions = pf + esi + income_tax + professional_tax + late_penalty
            net_salary = base_salary + total_allowances - total_deductions
            
            # Create salary slip record
            salary_slip = {
                "employee_id": emp_id,
                "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
                "department": employee.get("department", ""),
                "month": month,
                "year": int(year),
                "base_salary": base_salary,
                "allowances": {
                    "hra": hra,
                    "medical": medical_allowance,
                    "transport": transport_allowance,
                    "overtime": overtime_amount,
                    "bonus": bonus_amount
                },
                "total_allowances": total_allowances,
                "deductions": {
                    "pf": pf,
                    "esi": esi,
                    "income_tax": income_tax,
                    "professional_tax": professional_tax,
                    "late_penalty": late_penalty
                },
                "total_deductions": total_deductions,
                "net_salary": net_salary,
                "status": "processed",
                "generated_by": str(current_user.id),
                "generated_at": datetime.now(),
                "pay_date": None
            }
            
            payroll_records.append(salary_slip)
        
        # Insert all salary slips
        if payroll_records:
            result = salary_slips_collection.insert_many(payroll_records)
            
            return {
                "message": "Payroll generated successfully",
                "records_created": len(result.inserted_ids),
                "month": month,
                "year": year,
                "department": department
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employees found for payroll generation"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating payroll: {str(e)}"
        )

@router.get("/salary-slip/{employee_id}")
async def download_salary_slip(
    employee_id: str,
    month: str = Query(..., description="Month (01-12)"),
    year: int = Query(..., description="Year"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Download salary slip PDF for an employee"""
    if current_user.role not in ["director", "hr", "manager"] and str(current_user.id) != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this salary slip"
        )
    
    try:
        from app.database.salary_slips import salary_slips_collection
        from fastapi.responses import Response
        
        # Find the salary slip
        salary_slip = salary_slips_collection.find_one({
            "employee_id": employee_id,
            "month": month,
            "year": year
        })
        
        if not salary_slip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salary slip not found"
            )
        
        # Generate PDF (placeholder - you would use a PDF library like reportlab)
        pdf_content = f"""
        SALARY SLIP
        Employee: {salary_slip['employee_name']}
        Month/Year: {month}/{year}
        Base Salary: ₹{salary_slip['base_salary']:,.2f}
        Total Allowances: ₹{salary_slip['total_allowances']:,.2f}
        Total Deductions: ₹{salary_slip['total_deductions']:,.2f}
        Net Salary: ₹{salary_slip['net_salary']:,.2f}
        """.encode('utf-8')
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=salary_slip_{employee_id}_{month}_{year}.pdf"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating salary slip: {str(e)}"
        )

@router.put("/payroll/{employee_id}/mark-paid")
async def mark_payroll_as_paid(
    employee_id: str,
    payment_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Mark an employee's payroll as paid"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to mark payroll as paid"
        )
    
    try:
        from app.database.salary_slips import salary_slips_collection
        
        month = payment_data.get("month")
        year = payment_data.get("year")
        
        result = salary_slips_collection.update_one(
            {
                "employee_id": employee_id,
                "month": month,
                "year": int(year)
            },
            {
                "$set": {
                    "status": "paid",
                    "pay_date": datetime.now(),
                    "paid_by": str(current_user.id)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll record not found"
            )
        
        return {"message": "Payroll marked as paid successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking payroll as paid: {str(e)}"
        )

@router.get("/salary-slips/bulk")
async def download_bulk_salary_slips(
    month: str = Query(..., description="Month (01-12)"),
    year: int = Query(..., description="Year"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Download bulk salary slips as ZIP file"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download bulk salary slips"
        )
    
    try:
        from app.database.salary_slips import salary_slips_collection
        from fastapi.responses import Response
        import zipfile
        import io
        
        # Find all salary slips for the period
        query = {"month": month, "year": year}
        if department:
            query["department"] = department
        
        salary_slips = list(salary_slips_collection.find(query))
        
        if not salary_slips:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No salary slips found for the specified period"
            )
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for slip in salary_slips:
                # Generate PDF content for each slip (placeholder)
                pdf_content = f"""
                SALARY SLIP
                Employee: {slip['employee_name']}
                Month/Year: {month}/{year}
                Base Salary: ₹{slip['base_salary']:,.2f}
                Total Allowances: ₹{slip['total_allowances']:,.2f}
                Total Deductions: ₹{slip['total_deductions']:,.2f}
                Net Salary: ₹{slip['net_salary']:,.2f}
                """.encode('utf-8')
                
                filename = f"salary_slip_{slip['employee_id']}_{month}_{year}.pdf"
                zip_file.writestr(filename, pdf_content)
        
        zip_buffer.seek(0)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bulk_salary_slips_{month}_{year}.zip"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating bulk salary slips: {str(e)}"
        )
