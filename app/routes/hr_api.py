from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from typing import List, Optional
from app.utils.auth import get_current_user
from app.database.users import UserInDB, DatabaseUsers
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

# Employee Management
@router.get("/employees", response_model=List[dict])
async def get_all_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by employee status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all employees (HR only)"""
    if current_user.role not in ["director", "hr"]:
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

@router.get("/employees/{employee_id}")
async def get_employee_by_id(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get employee details by ID"""
    if current_user.role not in ["director", "hr"]:
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
    if current_user.role not in ["director", "hr"]:
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
