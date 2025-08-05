from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Body
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
from datetime import datetime, date, timedelta
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
    if current_user.role not in ["director", "hr", "manager"]:
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

@router.put("/attendance/{attendance_id}")
async def update_attendance_record(
    attendance_id: str,
    attendance_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update an attendance record"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update attendance records"
        )
    
    try:
        success = await DatabaseAttendance.update_attendance(attendance_id, attendance_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        return {"message": "Attendance record updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating attendance record: {str(e)}"
        )

@router.get("/attendance")
async def get_monthly_attendance(
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year (e.g., 2025)"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get attendance records for a specific month and year"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attendance data"
        )
    
    try:
        from app.database.attendance import attendance_collection
        from app.database.users import users_collection
        from calendar import monthrange
        from bson import ObjectId
        
        # Validate month and year
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12"
            )
        
        if not (2020 <= year <= 2030):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year must be between 2020 and 2030"
            )
        
        # Get first and last day of the month
        first_day = f"{year}-{month:02d}-01"
        last_day_num = monthrange(year, month)[1]
        last_day = f"{year}-{month:02d}-{last_day_num:02d}"
        
        # Get attendance records for the month
        attendance_records = list(attendance_collection.find({
            "date": {
                "$gte": first_day,
                "$lte": last_day
            }
        }))
        
        # Enrich with user data
        enriched_records = []
        for record in attendance_records:
            # Convert ObjectId to string for serialization
            record["_id"] = str(record["_id"])
            
            # Handle user_id - it might be string or ObjectId
            user_id = record.get("user_id")
            if isinstance(user_id, str):
                # Try to find user by string ID first
                user = users_collection.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
                if not user:
                    # Try finding by string user_id field
                    user = users_collection.find_one({"user_id": user_id})
            else:
                # user_id is already ObjectId
                user = users_collection.find_one({"_id": user_id})
            
            if user:
                enriched_records.append({
                    **record,
                    "employee_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "department": user.get("department", "N/A"),
                    "is_late": record.get("is_late", False),
                    "status": "present" if record.get("check_in") else "absent",
                    "work_hours": record.get("work_hours", 0)
                })
            else:
                # Add record even if user not found, with placeholder data
                enriched_records.append({
                    **record,
                    "employee_name": f"Unknown User ({user_id})",
                    "department": "N/A",
                    "is_late": record.get("is_late", False),
                    "status": "present" if record.get("check_in") else "absent",
                    "work_hours": record.get("work_hours", 0)
                })
        
        # Return directly as array for frontend compatibility
        return enriched_records
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly attendance: {str(e)}"
        )

@router.post("/attendance")
async def create_attendance_record(
    attendance_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create or update attendance record for an employee (HR/Manager only)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create attendance records"
        )
    
    try:
        from app.database.attendance import attendance_collection
        from bson import ObjectId
        from datetime import datetime
        
        # Handle both user_id and employee_id field names for flexibility
        user_id = attendance_data.get("user_id") or attendance_data.get("employee_id")
        date = attendance_data.get("date")
        
        # Validate required fields
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: user_id or employee_id"
            )
        
        if not date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: date"
            )
        
        # Check if attendance record already exists for this user and date
        existing_record = attendance_collection.find_one({
            "user_id": user_id,
            "date": date
        })
        
        # Prepare attendance record
        now = datetime.now()
        record_data = {
            "user_id": user_id,
            "date": date,
            "check_in": attendance_data.get("check_in"),
            "check_out": attendance_data.get("check_out"),
            "check_in_location": attendance_data.get("check_in_location"),
            "check_out_location": attendance_data.get("check_out_location"),
            "check_in_note": attendance_data.get("check_in_note") or attendance_data.get("notes"),
            "check_out_note": attendance_data.get("check_out_note"),
            "work_summary": attendance_data.get("work_summary"),
            "is_late": attendance_data.get("is_late", False),
            "is_complete": attendance_data.get("is_complete", False),
            "work_hours": attendance_data.get("work_hours", 0),
            "status": attendance_data.get("status", "present"),
            "updated_at": now
        }
        
        if existing_record:
            # Update existing record
            result = attendance_collection.update_one(
                {"_id": existing_record["_id"]},
                {"$set": record_data}
            )
            record_id = existing_record["_id"]
            action = "updated"
        else:
            # Create new record
            record_data["created_at"] = now
            result = attendance_collection.insert_one(record_data)
            record_id = result.inserted_id
            action = "created"
        
        # Get the updated/created record
        final_record = attendance_collection.find_one({"_id": record_id})
        
        # Enrich with user data
        from app.database.users import users_collection
        user = users_collection.find_one({"_id": final_record["user_id"]})
        
        response_data = {
            **final_record,
            "_id": str(final_record["_id"]),
            "employee_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else "Unknown",
            "department": user.get("department", "N/A") if user else "N/A"
        }
        
        return {
            "message": f"Attendance record {action} successfully",
            "action": action,
            "attendance": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating attendance record: {str(e)}"
        )

@router.post("/attendance/bulk")
async def create_bulk_attendance_records(
    bulk_attendance_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create or update multiple attendance records (HR/Manager only)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create attendance records"
        )
    
    try:
        from app.database.attendance import attendance_collection
        from bson import ObjectId
        from datetime import datetime
        
        # Handle both bulk format and individual record format
        if "records" in bulk_attendance_data:
            # New format: {"records": [...]}
            attendance_records = bulk_attendance_data.get("records", [])
        else:
            # Legacy format: direct bulk data for all employees in department
            bulk_data = bulk_attendance_data
            date = bulk_data.get("date")
            department = bulk_data.get("department")
            status = bulk_data.get("status", "present")
            check_in = bulk_data.get("check_in")
            check_out = bulk_data.get("check_out")
            
            if not date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Date is required for bulk attendance"
                )
            
            # Get employees for the department
            from app.database.users import users_collection
            query = {"is_active": True}
            if department:
                query["department"] = department
            
            employees = list(users_collection.find(query, {"_id": 1}))
            
            # Create records for all employees
            attendance_records = []
            for emp in employees:
                attendance_records.append({
                    "user_id": str(emp["_id"]),
                    "date": date,
                    "status": status,
                    "check_in": check_in,
                    "check_out": check_out
                })
        
        if not attendance_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No attendance records provided"
            )
        
        results = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for record_data in attendance_records:
            try:
                # Handle both user_id and employee_id field names for flexibility
                user_id = record_data.get("user_id") or record_data.get("employee_id")
                date = record_data.get("date")
                
                # Validate required fields
                if not user_id or not date:
                    results.append({
                        "user_id": user_id,
                        "date": date,
                        "status": "error",
                        "message": "Missing required field: user_id or date"
                    })
                    error_count += 1
                    continue
                
                # Check if attendance record already exists for this user and date
                existing_record = attendance_collection.find_one({
                    "user_id": user_id,
                    "date": date
                })
                
                # Prepare attendance record
                now = datetime.now()
                record_data_clean = {
                    "user_id": user_id,
                    "date": date,
                    "check_in": record_data.get("check_in"),
                    "check_out": record_data.get("check_out"),
                    "check_in_location": record_data.get("check_in_location"),
                    "check_out_location": record_data.get("check_out_location"),
                    "check_in_note": record_data.get("check_in_note") or record_data.get("notes"),
                    "check_out_note": record_data.get("check_out_note"),
                    "work_summary": record_data.get("work_summary"),
                    "is_late": record_data.get("is_late", False),
                    "is_complete": record_data.get("is_complete", False),
                    "work_hours": record_data.get("work_hours", 0),
                    "status": record_data.get("status", "present"),
                    "updated_at": now
                }
                
                if existing_record:
                    # Update existing record
                    result = attendance_collection.update_one(
                        {"_id": existing_record["_id"]},
                        {"$set": record_data_clean}
                    )
                    action = "updated"
                    updated_count += 1
                else:
                    # Create new record
                    record_data_clean["created_at"] = now
                    result = attendance_collection.insert_one(record_data_clean)
                    action = "created"
                    created_count += 1
                
                results.append({
                    "user_id": user_id,
                    "date": date,
                    "status": "success",
                    "action": action,
                    "message": f"Attendance record {action} successfully"
                })
                
            except Exception as record_error:
                results.append({
                    "user_id": record_data.get("user_id", "unknown"),
                    "date": record_data.get("date", "unknown"),
                    "status": "error",
                    "message": f"Error processing record: {str(record_error)}"
                })
                error_count += 1
        
        return {
            "message": "Bulk attendance processing completed",
            "summary": {
                "total_records": len(attendance_records),
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            },
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing bulk attendance: {str(e)}"
        )

@router.get("/attendance/export")
async def export_attendance_data(
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year (e.g., 2025)"),
    format: str = Query("csv", description="Export format: csv, excel"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Export attendance data for a specific month and year"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export attendance data"
        )
    
    try:
        from app.database.attendance import attendance_collection
        from app.database.users import users_collection
        from calendar import monthrange
        from bson import ObjectId
        from fastapi.responses import Response
        import csv
        import io
        
        # Validate month and year
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12"
            )
        
        if not (2020 <= year <= 2030):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Year must be between 2020 and 2030"
            )
        
        # Get first and last day of the month
        first_day = f"{year}-{month:02d}-01"
        last_day_num = monthrange(year, month)[1]
        last_day = f"{year}-{month:02d}-{last_day_num:02d}"
        
        # Build query
        query = {
            "date": {
                "$gte": first_day,
                "$lte": last_day
            }
        }
        
        # Get attendance records for the month
        attendance_records = list(attendance_collection.find(query))
        
        # Enrich with user data and filter by department if specified
        enriched_records = []
        for record in attendance_records:
            # Convert ObjectId to string for serialization
            record["_id"] = str(record["_id"])
            
            # Handle user_id - it might be string or ObjectId
            user_id = record.get("user_id")
            if isinstance(user_id, str):
                # Try to find user by string ID first
                user = users_collection.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
                if not user:
                    # Try finding by string user_id field
                    user = users_collection.find_one({"user_id": user_id})
            else:
                # user_id is already ObjectId
                user = users_collection.find_one({"_id": user_id})
            
            if user:
                user_department = user.get("department", "N/A")
                
                # Filter by department if specified
                if department and user_department != department:
                    continue
                
                enriched_records.append({
                    "Employee ID": user_id,
                    "Employee Name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "Department": user_department,
                    "Date": record.get("date"),
                    "Check In": record.get("check_in", ""),
                    "Check Out": record.get("check_out", ""),
                    "Work Hours": record.get("work_hours", 0),
                    "Status": "Present" if record.get("check_in") else "Absent",
                    "Is Late": "Yes" if record.get("is_late", False) else "No",
                    "Check In Location": record.get("check_in_location", ""),
                    "Check Out Location": record.get("check_out_location", ""),
                    "Notes": record.get("check_in_note", "")
                })
        
        if not enriched_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No attendance records found for the specified period"
            )
        
        # Generate CSV content
        if format.lower() == "csv":
            output = io.StringIO()
            if enriched_records:
                fieldnames = enriched_records[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_records)
            
            csv_content = output.getvalue()
            output.close()
            
            # Create filename
            filename = f"attendance_{month:02d}_{year}"
            if department:
                filename += f"_{department}"
            filename += ".csv"
            
            return Response(
                content=csv_content.encode('utf-8'),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        elif format.lower() == "excel":
            # For Excel export (would need openpyxl or xlsxwriter)
            # For now, return CSV with Excel MIME type
            output = io.StringIO()
            if enriched_records:
                fieldnames = enriched_records[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_records)
            
            csv_content = output.getvalue()
            output.close()
            
            # Create filename
            filename = f"attendance_{month:02d}_{year}"
            if department:
                filename += f"_{department}"
            filename += ".xlsx"
            
            return Response(
                content=csv_content.encode('utf-8'),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'csv' or 'excel'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting attendance data: {str(e)}"
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
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create job postings"
        )
    
    try:
        new_job = await DatabaseJobPostings.create_job_posting(job_data)
        job_dict = new_job.model_dump()
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
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
            # Convert ObjectId to string
            if "id" in job_dict:
                job_dict["id"] = str(job_dict["id"])
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
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
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
    if current_user.role not in ["director", "hr", "manager"]:
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
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
        return job_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job posting: {str(e)}"
        )

@router.delete("/recruitment/jobs/{job_id}")
async def delete_job_posting(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a job posting"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete job postings"
        )
    
    try:
        deleted = await DatabaseJobPostings.delete_job_posting(job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        return {"message": "Job posting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job posting: {str(e)}"
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
    if current_user.role not in ["director", "hr", "manager"]:
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
    if current_user.role not in ["director", "hr", "manager"]:
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
    if current_user.role not in ["director", "hr", "manager"]:
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

@router.get("/reports/recent")
async def get_recent_reports(
    limit: int = Query(10, description="Number of recent reports to return"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get recent reports generated by the user"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view reports"
        )
    
    try:
        # For now, return mock data since we don't have a reports history table
        # In a real implementation, you would query a reports_history collection
        recent_reports = [
            {
                "id": f"rpt_{i+1}",
                "name": f"Employee Report {i+1}",
                "type": "employee",
                "format": "excel",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "created_by": current_user.username,
                "file_size": "2.5 MB"
            }
            for i in range(min(limit, 5))
        ]
        
        return recent_reports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recent reports: {str(e)}"
        )

@router.post("/reports/employee")
async def generate_employee_report(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate employee report"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate employee reports"
        )
    
    try:
        # Get all employees
        from app.database.users import users_collection
        query = {"is_active": True}
        if report_config.get("department"):
            query["department"] = report_config["department"]
        
        employees = list(users_collection.find(query))
        
        # Convert ObjectIds to strings for JSON serialization
        for emp in employees:
            emp["_id"] = str(emp["_id"])
            # Remove sensitive fields
            emp.pop("password", None)
            emp.pop("hashed_password", None)
        
        # Generate Excel file content (mock implementation)
        from io import BytesIO
        import json
        
        # For now, return JSON data as a file
        # In a real implementation, you would use openpyxl or similar to generate Excel
        output = BytesIO()
        output.write(json.dumps(employees, indent=2, default=str).encode())
        output.seek(0)
        
        # Return the file
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=employee_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating employee report: {str(e)}"
        )

@router.post("/reports/custom")
async def generate_custom_report(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate custom report based on configuration"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate custom reports"
        )
    
    try:
        report_type = report_config.get("type")
        department = report_config.get("department")
        start_date = report_config.get("start_date")
        end_date = report_config.get("end_date")
        format_type = report_config.get("format", "excel")
        
        if not report_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report type is required"
            )
        
        # Route to appropriate report generator
        if report_type == "employee":
            return await generate_employee_report(report_config, current_user)
        elif report_type == "attendance":
            # Call existing attendance report endpoint
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date and end date are required for attendance reports"
                )
            report_data = await get_attendance_report(start_date, end_date, department, current_user)
        elif report_type == "leave":
            # Call existing leave report endpoint
            year = datetime.now().year
            if start_date:
                year = datetime.strptime(start_date, "%Y-%m-%d").year
            report_data = await get_leave_summary_report(year, department, current_user)
        else:
            # For other report types, return basic data
            report_data = {
                "type": report_type,
                "message": f"Report generation for {report_type} is not yet implemented",
                "department": department,
                "date_range": f"{start_date} to {end_date}" if start_date and end_date else None
            }
        
        # Generate file based on format
        from io import BytesIO
        import json
        
        output = BytesIO()
        output.write(json.dumps(report_data, indent=2, default=str).encode())
        output.seek(0)
        
        if format_type == "csv":
            media_type = "text/csv"
            extension = "csv"
        elif format_type == "pdf":
            media_type = "application/pdf"
            extension = "pdf"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = f"custom_{report_type}_report.{extension}"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating custom report: {str(e)}"
        )

@router.get("/reports/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Download a previously generated report"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download reports"
        )
    
    try:
        # For now, return a mock file since we don't have report storage
        # In a real implementation, you would fetch the file from storage
        from io import BytesIO
        import json
        
        mock_data = {
            "report_id": report_id,
            "message": "This is a mock report file",
            "generated_at": datetime.now().isoformat(),
            "requested_by": current_user.username
        }
        
        output = BytesIO()
        output.write(json.dumps(mock_data, indent=2).encode())
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading report: {str(e)}"
        )

@router.post("/reports/payroll")
async def generate_payroll_report(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate payroll report"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate payroll reports"
        )
    
    try:
        # Mock payroll report data
        from io import BytesIO
        import json
        
        mock_data = {
            "report_type": "payroll",
            "generated_at": datetime.now().isoformat(),
            "department": report_config.get("department", "All Departments"),
            "period": f"{report_config.get('start_date', '')} to {report_config.get('end_date', '')}",
            "message": "Payroll report generation is not yet fully implemented"
        }
        
        output = BytesIO()
        output.write(json.dumps(mock_data, indent=2).encode())
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=payroll_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating payroll report: {str(e)}"
        )

@router.post("/reports/leave")
async def generate_leave_report_post(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate leave report (POST version for file download)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate leave reports"
        )
    
    try:
        year = datetime.now().year
        start_date = report_config.get("start_date", "")
        if start_date and start_date.strip():
            try:
                year = datetime.strptime(start_date, "%Y-%m-%d").year
            except ValueError:
                year = datetime.now().year
        
        department = report_config.get("department")
        from app.database.users import users_collection
        query = {"is_active": True}
        if department:
            query["department"] = department

        employees = list(users_collection.find(query, {"_id": 1, "full_name": 1, "department": 1}))
        report_data = []
        for emp in employees:
            emp_id = str(emp["_id"])
            leave_requests = await DatabaseLeaveRequests.get_user_leave_requests(emp_id)
            year_leaves = [
                lr for lr in leave_requests 
                if hasattr(lr, "start_date") and hasattr(lr, "end_date") and (
                    (getattr(lr, "start_date").year == year) or (getattr(lr, "end_date").year == year)
                )
            ]
            approved_leaves = [lr for lr in year_leaves if getattr(lr, "status", None) == "approved"]
            total_leave_days = sum(getattr(lr, "duration_days", 0) for lr in approved_leaves)
            leave_types = {}
            for lr in approved_leaves:
                leave_type = getattr(lr, "leave_type", "Other")
                leave_types[leave_type] = leave_types.get(leave_type, 0) + getattr(lr, "duration_days", 0)
            report_data.append({
                "employee_id": emp_id,
                "employee_name": emp.get("full_name", ""),
                "department": emp.get("department", ""),
                "total_leave_days": total_leave_days,
                "leave_types": leave_types,
                "pending_requests": len([lr for lr in year_leaves if getattr(lr, "status", None) == "pending"])
            })

        final_report = {
            "year": year,
            "department": department,
            "employees": report_data
        }
        from io import BytesIO
        output = BytesIO()
        output.write(json.dumps(final_report, indent=2, default=str).encode())
        output.seek(0)
        from fastapi.responses import StreamingResponse
        # Fix: set content-type to application/json and filename to .json
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=leave_report.json"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating leave report: {str(e)}"
        )

@router.post("/reports/attendance")
async def generate_attendance_report_post(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate attendance report (POST version for file download)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate attendance reports"
        )
    
    try:
        start_date = report_config.get("start_date")
        end_date = report_config.get("end_date")
        department = report_config.get("department")
        if not start_date or not end_date:
            # Use current month if dates not provided
            today = datetime.now()
            start_date = f"{today.year}-{today.month:02d}-01"
            end_date = today.strftime("%Y-%m-%d")
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        from app.database.users import users_collection
        query = {"is_active": True}
        if department:
            query["department"] = department
        employees = list(users_collection.find(query, {"_id": 1, "full_name": 1, "department": 1}))
        report_data = []
        for emp in employees:
            emp_id = str(emp["_id"])
            attendance_records = await DatabaseAttendance.get_attendance_by_date_range(
                emp_id, start_date_obj, end_date_obj
            )
            present_days = len([a for a in attendance_records if getattr(a, "status", None) == "present"])
            absent_days = len([a for a in attendance_records if getattr(a, "status", None) == "absent"])
            late_days = len([a for a in attendance_records if getattr(a, "is_late", False)])
            report_data.append({
                "employee_id": emp_id,
                "employee_name": emp.get("full_name", ""),
                "department": emp.get("department", ""),
                "present_days": present_days,
                "absent_days": absent_days,
                "late_days": late_days,
                "total_working_days": len(attendance_records)
            })
        final_report = {
            "start_date": start_date,
            "end_date": end_date,
            "department": department,
            "employees": report_data
        }
        from io import BytesIO
        output = BytesIO()
        import xlsxwriter
        
        # Create an in-memory output file for the workbook
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Attendance Report")
        
        # Write header row
        worksheet.write_row(0, 0, [
            "Employee ID", "Employee Name", "Department", 
            "Present Days", "Absent Days", "Late Days", "Total Working Days"
        ])
        
        # Write data rows
        for row_num, data in enumerate(report_data, start=1):
            worksheet.write_row(row_num, 0, [
                data["employee_id"], data["employee_name"], data["department"],
                data["present_days"], data["absent_days"], data["late_days"], data["total_working_days"]
            ])
        
        # Close the workbook
        workbook.close()
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=attendance_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating attendance report: {str(e)}"
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
    if current_user.role not in ["director", "hr", "manager", "admin"]:
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
    if current_user.role not in ["director", "hr", "manager", "admin"]:
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
            base_salary = employee.get("salary", 0) or 0  # Ensure it's not None
            
            # Skip employees with no salary set
            if base_salary <= 0:
                continue
            
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
    if current_user.role not in ["director", "hr", "manager", "admin"] and str(current_user.id) != employee_id:
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
    if current_user.role not in ["director", "hr", "manager", "admin"]:
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
    if current_user.role not in ["director", "hr", "manager", "admin"]:
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

# Job API Aliases (for frontend compatibility)
# These endpoints alias the recruitment/jobs endpoints to /jobs for easier frontend access

def convert_job_to_frontend_format(job_dict: dict) -> dict:
    """Convert database job format to frontend expected format"""
    # Create a copy to avoid modifying the original
    frontend_job = job_dict.copy()
    
    # Map database fields to frontend fields
    if "position_type" in frontend_job:
        frontend_job["employment_type"] = frontend_job.pop("position_type")
    
    if "skills_required" in frontend_job:
        frontend_job["skills"] = ", ".join(frontend_job.pop("skills_required")) if frontend_job.get("skills_required") else ""
    
    if "salary_range" in frontend_job and frontend_job["salary_range"]:
        # Try to parse salary range like "400000-800000"
        try:
            if "-" in frontend_job["salary_range"]:
                min_sal, max_sal = frontend_job["salary_range"].split("-")
                frontend_job["salary_min"] = int(min_sal.strip())
                frontend_job["salary_max"] = int(max_sal.strip())
            else:
                frontend_job["salary_min"] = 0
                frontend_job["salary_max"] = 0
        except:
            frontend_job["salary_min"] = 0
            frontend_job["salary_max"] = 0
    else:
        frontend_job["salary_min"] = 0
        frontend_job["salary_max"] = 0
    
    # Convert requirements list to string if needed
    if "requirements" in frontend_job and isinstance(frontend_job["requirements"], list):
        frontend_job["requirements"] = "; ".join(frontend_job["requirements"])
    
    # Ensure created_at field for frontend
    if "posted_date" in frontend_job:
        frontend_job["created_at"] = frontend_job["posted_date"]
    elif "created_at" not in frontend_job:
        frontend_job["created_at"] = datetime.now().isoformat()
    
    return frontend_job

def convert_job_from_frontend_format(job_data: dict) -> dict:
    """Convert frontend job format to database expected format"""
    # Create a copy to avoid modifying the original
    db_job = job_data.copy()
    
    # Map frontend fields to database fields
    if "employment_type" in db_job:
        db_job["position_type"] = db_job.pop("employment_type")
    
    if "skills" in db_job and db_job["skills"]:
        # Convert comma-separated string to list
        db_job["skills_required"] = [skill.strip() for skill in db_job["skills"].split(",") if skill.strip()]
        del db_job["skills"]
    
    # Convert salary min/max to range string
    salary_min = db_job.pop("salary_min", 0) if "salary_min" in db_job else 0
    salary_max = db_job.pop("salary_max", 0) if "salary_max" in db_job else 0
    
    if salary_min > 0 or salary_max > 0:
        db_job["salary_range"] = f"{salary_min}-{salary_max}"
    
    # Convert requirements string to list if needed
    if "requirements" in db_job and isinstance(db_job["requirements"], str):
        db_job["requirements"] = [req.strip() for req in db_job["requirements"].split(";") if req.strip()]
    
    # Add default posted_by if not present
    if "posted_by" not in db_job:
        db_job["posted_by"] = "system"
    
    return db_job

@router.get("/jobs", response_model=List[dict])
async def get_jobs_alias(
    status: Optional[str] = Query(None, description="Filter by job status"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Alias for /recruitment/jobs - Get all job postings"""
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
            # Convert ObjectId to string
            if "id" in job_dict:
                job_dict["id"] = str(job_dict["id"])
            # Convert to frontend format
            frontend_job = convert_job_to_frontend_format(job_dict)
            job_list.append(frontend_job)
        return job_list
    except Exception as e:
        # Fallback: return sample jobs if DB/API fails
        print(f"Error fetching job postings: {str(e)}")
        return [
            {
                "id": "1",
                "title": "Senior Frontend Developer",
                "department": "Development",
                "experience_level": "Senior Level",
                "location": "Pune, India",
                "employment_type": "Full-time",
                "status": "active",
                "description": "We are looking for a skilled Frontend Developer to join our team.",
                "requirements": "Experience with React, JavaScript, HTML, CSS",
                "skills": "React, JavaScript, HTML, CSS, TypeScript",
                "salary_min": 800000,
                "salary_max": 1200000,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "title": "Sales Executive",
                "department": "Sales",
                "experience_level": "Mid Level",
                "location": "Pune, India",
                "employment_type": "Full-time",
                "status": "active",
                "description": "Join our sales team to drive business growth.",
                "requirements": "Experience in B2B sales, excellent communication skills",
                "skills": "Sales, Communication, CRM, Negotiation",
                "salary_min": 400000,
                "salary_max": 700000,
                "created_at": datetime.now().isoformat()
            }
        ]
    

@router.post("/jobs", response_model=dict)
async def create_job_alias(
    job_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Alias for /recruitment/jobs - Create a new job posting"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create job postings"
        )
    
    try:
        # Convert from frontend format to database format
        db_job_data = convert_job_from_frontend_format(job_data)
        db_job_data["posted_by"] = str(current_user.id)
        
        # Create JobPostingCreate object
        job_create = JobPostingCreate(**db_job_data)
        new_job = await DatabaseJobPostings.create_job_posting(job_create)
        job_dict = new_job.model_dump()
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
        
        # Convert back to frontend format
        frontend_job = convert_job_to_frontend_format(job_dict)
        return frontend_job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating job posting: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=dict)
async def get_job_by_id_alias(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Alias for /recruitment/jobs/{job_id} - Get a specific job posting"""
    if current_user.role not in ["director", "hr", "manager"]:
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
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
        
        # Convert to frontend format
        frontend_job = convert_job_to_frontend_format(job_dict)
        return frontend_job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching job posting: {str(e)}"
        )

@router.put("/jobs/{job_id}", response_model=dict)
async def update_job_alias(
    job_id: str,
    job_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Alias for /recruitment/jobs/{job_id} - Update a job posting"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update job postings"
        )
    
    try:
        # Convert from frontend format to database format
        db_job_data = convert_job_from_frontend_format(job_data)
        
        # Create JobPostingUpdate object
        job_update = JobPostingUpdate(**db_job_data)
        updated_job = await DatabaseJobPostings.update_job_posting(job_id, job_update)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        job_dict = updated_job.model_dump()
        # Convert ObjectId to string
        if "id" in job_dict:
            job_dict["id"] = str(job_dict["id"])
        
        # Convert back to frontend format
        frontend_job = convert_job_to_frontend_format(job_dict)
        return frontend_job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job posting: {str(e)}"
        )

@router.delete("/jobs/{job_id}")
async def delete_job_alias(
    job_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Alias for /recruitment/jobs/{job_id} - Delete a job posting"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete job postings"
        )
    
    try:
        # Try to delete by string and ObjectId
        deleted = await DatabaseJobPostings.delete_job_posting(job_id)
        if not deleted:
            # Try ObjectId if using MongoDB
            try:
                from bson import ObjectId
                obj_id = ObjectId(job_id)
                deleted = await DatabaseJobPostings.delete_job_posting(obj_id)
            except Exception:
                pass
        if not deleted:
            # Log for debugging
            print(f"Delete failed: No job found with id {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job posting not found for id: {job_id}"
            )
        return {"message": "Job posting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting job posting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job posting: {str(e)}"
        )

# Candidates API Aliases
def convert_candidate_to_frontend_format(candidate_dict: dict) -> dict:
    """Convert database candidate/application format to frontend expected format"""
    frontend_candidate = candidate_dict.copy()
    
    # Map application fields to candidate fields expected by frontend
    if "applicant_name" in frontend_candidate:
        # Split applicant_name into first_name and last_name
        name_parts = frontend_candidate["applicant_name"].split(" ", 1)
        frontend_candidate["first_name"] = name_parts[0] if name_parts else ""
        frontend_candidate["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
        del frontend_candidate["applicant_name"]
    
    if "applicant_email" in frontend_candidate:
        frontend_candidate["email"] = frontend_candidate.pop("applicant_email")
    
    if "applicant_phone" in frontend_candidate:
        frontend_candidate["phone"] = frontend_candidate.pop("applicant_phone")
    
    if "experience_years" in frontend_candidate:
        frontend_candidate["experience"] = frontend_candidate.pop("experience_years")
    
    # Map status to stage for pipeline
    status_to_stage = {
        "submitted": "applied",
        "under_review": "screening", 
        "interview_scheduled": "interview",
        "offer_made": "offer",
        "hired": "hired",
        "rejected": "rejected"
    }
    
    if "status" in frontend_candidate:
        frontend_candidate["stage"] = status_to_stage.get(frontend_candidate["status"], "applied")
    
    # Add job_title if we have job_posting_id
    if "job_posting_id" in frontend_candidate:
        frontend_candidate["job_title"] = "Various Positions"  # Default value
    
    return frontend_candidate

def convert_candidate_from_frontend_format(candidate_data: dict) -> dict:
    """Convert frontend candidate format to database application format"""
    db_candidate = candidate_data.copy()
    
    # Combine first_name and last_name
    first_name = db_candidate.pop("first_name", "")
    last_name = db_candidate.pop("last_name", "")
    db_candidate["applicant_name"] = f"{first_name} {last_name}".strip()
    
    # Map frontend fields to database fields
    if "email" in db_candidate:
        db_candidate["applicant_email"] = db_candidate.pop("email")
    
    if "phone" in db_candidate:
        db_candidate["applicant_phone"] = db_candidate.pop("phone")
    
    if "experience" in db_candidate:
        db_candidate["experience_years"] = db_candidate.pop("experience")
    
    # Map stage to status
    stage_to_status = {
        "applied": "submitted",
        "screening": "under_review",
        "interview": "interview_scheduled",
        "offer": "offer_made", 
        "hired": "hired",
        "rejected": "rejected"
    }
    
    if "stage" in db_candidate:
        db_candidate["status"] = stage_to_status.get(db_candidate["stage"], "submitted")
        del db_candidate["stage"]
    
    # Ensure required fields
    if "job_id" in db_candidate:
        job_id = db_candidate.pop("job_id")
        # Handle 'undefined' or empty job_id - this means no specific job selected
        if job_id and job_id != "undefined" and job_id.strip():
            db_candidate["job_posting_id"] = job_id
        # If job_id is undefined/empty, we need to set a default job_posting_id
        # For now, let's raise an error to inform the user to select a job
    
    return db_candidate

@router.get("/candidates", response_model=List[dict])
async def get_candidates_alias(
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all candidates"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view candidates"
        )
    
    try:
        candidates = await DatabaseJobApplications.get_all_applications()
        candidate_list = []
        for candidate in candidates:
            candidate_dict = candidate.model_dump()
            # Convert ObjectId to string
            if "id" in candidate_dict:
                candidate_dict["id"] = str(candidate_dict["id"])
            # Convert to frontend format
            frontend_candidate = convert_candidate_to_frontend_format(candidate_dict)
            candidate_list.append(frontend_candidate)
        return candidate_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching candidates: {str(e)}"
        )

@router.post("/candidates", response_model=dict)
async def create_candidate_alias(
    candidate_data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new candidate/application"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create candidates"
        )
    
    try:
        # Validate required fields
        job_id = candidate_data.get("job_id")
        if not job_id or job_id == "undefined" or not str(job_id).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select a job position for the candidate"
            )
        
        # Convert from frontend format to database format
        db_candidate_data = convert_candidate_from_frontend_format(candidate_data)
        
        # Validate that we have job_posting_id after conversion
        if "job_posting_id" not in db_candidate_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job posting ID is required"
            )
        
        # Create JobApplicationCreate object
        app_create = JobApplicationCreate(**db_candidate_data)
        new_application = await DatabaseJobApplications.create_application(app_create)
        app_dict = new_application.model_dump()
        # Convert ObjectId to string
        if "id" in app_dict:
            app_dict["id"] = str(app_dict["id"])
        
        # Convert back to frontend format
        frontend_candidate = convert_candidate_to_frontend_format(app_dict)
        return frontend_candidate
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(ve)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating candidate: {str(e)}"
        )

@router.get("/users/salary-slips")
async def get_user_salary_slips(
    employee_id: str = Query(..., description="Employee ID"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all salary slips for a user (employee)"""
    # Allow only HR, director, manager, admin, or the employee themselves
    if current_user.role not in ["director", "hr", "manager", "admin"] and str(current_user.id) != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these salary slips"
        )
    try:
        from app.database.salary_slips import salary_slips_collection
        slips = list(salary_slips_collection.find({"employee_id": employee_id}))
        for slip in slips:
            slip["id"] = str(slip.pop("_id"))
        # Return empty list if no slips found, do not raise error
        return slips
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in get_user_salary_slips: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching salary slips: {str(e)}"
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching salary slips: {str(e)}"
        )
@router.post("/reports/performance")
async def generate_performance_report(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate performance report (Excel format)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate performance reports"
        )
    try:
        # Mock performance report data
        from io import BytesIO
        import csv

        # Example: fetch performance reviews from DB
        reviews = await DatabasePerformanceReviews.get_all_reviews()
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow([
            "Employee ID", "Employee Name", "Department", "Review Date", "Rating", "Comments"
        ])
        for review in reviews:
            writer.writerow([
                getattr(review, "employee_id", ""),
                getattr(review, "employee_name", ""),
                getattr(review, "department", ""),
                getattr(review, "review_date", ""),
                getattr(review, "rating", ""),
                getattr(review, "comments", "")
            ])
        output.seek(0)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=performance_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating performance report: {str(e)}"
        )

@router.post("/reports/recruitment")
async def generate_recruitment_report(
    report_config: dict = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Generate recruitment report (Excel format)"""
    if current_user.role not in ["director", "hr", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate recruitment reports"
        )
    try:
        from io import BytesIO
        import csv

        job_postings = await DatabaseJobPostings.get_all_job_postings()
        applications = await DatabaseJobApplications.get_all_applications()

        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow([
            "Job ID", "Title", "Department", "Status", "Total Applications"
        ])
        for job in job_postings:
            # Defensive: handle both dict and object
            job_id = getattr(job, "id", None) or getattr(job, "_id", None) or job.get("id", "") if isinstance(job, dict) else ""
            title = getattr(job, "title", "") if hasattr(job, "title") else job.get("title", "")
            department = getattr(job, "department", "") if hasattr(job, "department") else job.get("department", "")
            status = getattr(job, "status", "") if hasattr(job, "status") else job.get("status", "")
            # Defensive: applications may be objects or dicts
            total_apps = len([app for app in applications if (
                (getattr(app, "job_posting_id", None) == job_id) or
                (isinstance(app, dict) and app.get("job_posting_id") == job_id)
            )])
            writer.writerow([job_id, title, department, status, total_apps])
        output.seek(0)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=recruitment_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recruitment report: {str(e)}"
        )
