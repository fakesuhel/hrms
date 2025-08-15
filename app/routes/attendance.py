from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional

from app.database.attendance import AttendanceCheckIn, AttendanceCheckOut, AttendanceResponse, DatabaseAttendance
from app.utils.auth import get_current_user
from app.utils.helpers import get_ist_now, get_ist_date_today, get_ist_date_iso

import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the helper function - this function just logs the IST time for debugging
def log_ist_now():
    """Log current datetime in IST timezone"""
    ist_now = get_ist_now()
    print(f"IST now: {ist_now}")
    logger.info(f"IST now: {ist_now}")
    return ist_now

# Log the current time for debugging
log_ist_now()

# def get_ist_now():
#     """Get current datetime in IST timezone"""
#     return datetime.now()

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
    responses={404: {"description": "Not found"}},
)

@router.post("/check-in", response_model=AttendanceResponse)
async def check_in(
    check_in_data: AttendanceCheckIn,
    current_user = Depends(get_current_user)
):
    try:
        # Add the current user's ID to the check-in data
        check_in_data.user_id = str(current_user.id)
        
        # If date is not provided, use today's date in IST
        if not check_in_data.date:
            check_in_data.date = get_ist_date_iso()
        
        # Debug logging
        print(f"Check-in request: User ID: {check_in_data.user_id}, Date: {check_in_data.date}")
        
        attendance = await DatabaseAttendance.check_in(check_in_data)
        
        # Convert attendance to AttendanceResponse
        response_dict = {
            "_id": str(attendance.id),
            "user_id": str(attendance.user_id),
            "date": attendance.date,
            "check_in": attendance.check_in,
            "check_out": attendance.check_out,
            "check_in_location": attendance.check_in_location,
            "check_out_location": attendance.check_out_location,
            "check_in_note": attendance.check_in_note,
            "check_out_note": attendance.check_out_note,
            "work_summary": attendance.work_summary,
            "is_late": attendance.is_late,
            "is_complete": attendance.is_complete,
            "work_hours": attendance.work_hours,
            "status": attendance.status,
            "created_at": attendance.created_at,
            "updated_at": attendance.updated_at
        }
        
        return AttendanceResponse(**response_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in check_in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    checkout_data: AttendanceCheckOut,
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Check-out request: User ID: {current_user.id}")
        print(f"Current time (IST): {get_ist_now().strftime('%Y-%m-%d %H:%M:%S')}, User: {current_user.id}")
        
        attendance = await DatabaseAttendance.check_out(
            str(current_user.id),
            checkout_data
        )
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active check-in found for today"
            )
        
        # Convert attendance to AttendanceResponse
        response_dict = {
            "_id": str(attendance.id),
            "user_id": str(attendance.user_id),
            "date": attendance.date,
            "check_in": attendance.check_in,
            "check_out": attendance.check_out,
            "check_in_location": attendance.check_in_location,
            "check_out_location": attendance.check_out_location,
            "check_in_note": attendance.check_in_note,
            "check_out_note": attendance.check_out_note,
            "work_summary": attendance.work_summary,
            "is_late": attendance.is_late,
            "is_complete": attendance.is_complete,
            "work_hours": attendance.work_hours,
            "status": attendance.status,
            "created_at": attendance.created_at,
            "updated_at": attendance.updated_at
        }
        
        return AttendanceResponse(**response_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in check_out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/history", response_model=List[AttendanceResponse])
async def get_attendance_history(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    try:
        # Default to last 30 days if dates not provided
        if not start_date:
            start_date = get_ist_date_today() - timedelta(days=30)
        if not end_date:
            end_date = get_ist_date_today()
        
        # Debug logging
        print(f"Getting attendance history: {start_date} to {end_date}")
        print(f"Current time (IST): {get_ist_now().strftime('%Y-%m-%d %H:%M:%S')}, User: {current_user.id}")
        
        attendances = await DatabaseAttendance.get_user_attendance(
            str(current_user.id),
            start_date,
            end_date
        )
        
        # Convert to AttendanceResponse objects
        result = []
        for attendance in attendances:
            try:
                response_dict = {
                    "_id": str(attendance.id),
                    "user_id": str(attendance.user_id),
                    "date": attendance.date,
                    "check_in": attendance.check_in,
                    "check_out": attendance.check_out,
                    "check_in_location": attendance.check_in_location,
                    "check_out_location": attendance.check_out_location,
                    "check_in_note": attendance.check_in_note,
                    "check_out_note": attendance.check_out_note,
                    "work_summary": attendance.work_summary,
                    "is_late": attendance.is_late,
                    "is_complete": attendance.is_complete,
                    "work_hours": attendance.work_hours,
                    "status": attendance.status,
                    "created_at": attendance.created_at,
                    "updated_at": attendance.updated_at
                }
                result.append(AttendanceResponse(**response_dict))
            except Exception as parse_error:
                print(f"Warning: Skipping invalid attendance record for response: {parse_error}")
                continue
        
        return result
        
    except Exception as e:
        print(f"Error in get_attendance_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance history: {str(e)}"
        )

@router.get("/team", response_model=List[AttendanceResponse])
async def get_team_attendance(
    for_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    try:
        # Debug logging
        print(f"Team attendance request: User: {current_user.username}, Role: {current_user.role}")
        
        # Case-insensitive role check
        user_role = str(current_user.role).lower().strip() if current_user.role else ""
        valid_roles = ['team_lead', 'teamlead', 'team lead', 'manager', 'admin']
        
        if not any(role.lower() == user_role or role.lower().replace(' ', '') == user_role.replace(' ', '')
                for role in valid_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access team attendance. Your role: {current_user.role}"
            )
        
        # Default to today if date not provided
        if not for_date:
            for_date = get_ist_date_today()
        
        # Get team members
        from app.database.users import DatabaseUsers
        team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
        
        if not team_members:
            # Return empty list if no team members found
            print(f"No team members found for manager {current_user.id}")
            return []
        
        team_ids = [str(member.id) for member in team_members]
        attendances = await DatabaseAttendance.get_team_attendance(team_ids, for_date)
        
        # Convert to AttendanceResponse objects
        result = []
        for attendance in attendances:
            response_dict = {
                "_id": str(attendance.id),
                "user_id": str(attendance.user_id),
                "date": attendance.date,
                "check_in": attendance.check_in,
                "check_out": attendance.check_out,
                "check_in_location": attendance.check_in_location if hasattr(attendance, 'check_in_location') else None,
                "check_out_location": attendance.check_out_location if hasattr(attendance, 'check_out_location') else None,
                "check_in_note": attendance.check_in_note if hasattr(attendance, 'check_in_note') else None,
                "check_out_note": attendance.check_out_note if hasattr(attendance, 'check_out_note') else None,
                "work_summary": attendance.work_summary if hasattr(attendance, 'work_summary') else None,
                "is_late": attendance.is_late if hasattr(attendance, 'is_late') else False,
                "is_complete": attendance.is_complete if hasattr(attendance, 'is_complete') else False,
                "work_hours": attendance.work_hours if hasattr(attendance, 'work_hours') else None,
                "status": attendance.status,
                "created_at": attendance.created_at,
                "updated_at": attendance.updated_at
            }
            result.append(AttendanceResponse(**response_dict))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_team_attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team attendance: {str(e)}"
        )

@router.get("/stats")
async def get_attendance_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user = Depends(get_current_user)
):
    try:
        # Default to current month if dates not provided
        if not start_date:
            today = get_ist_date_today()
            start_date = date(today.year, today.month, 1)
        if not end_date:
            end_date = get_ist_date_today()
        
        # Debug logging
        print(f"Getting attendance stats: {start_date} to {end_date}")
        print(f"Current time: 2025-06-12 06:56:11, User: soherunot")
        
        stats = await DatabaseAttendance.get_attendance_stats(
            str(current_user.id),
            start_date,
            end_date
        )
        
        # Add current timestamp and user info
        stats["timestamp"] = "2025-06-12 06:56:11"
        stats["user"] = "soherunot"
        
        return stats
        
    except Exception as e:
        print(f"Error in get_attendance_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance statistics: {str(e)}"
        )

@router.get("/", response_model=List[AttendanceResponse])
async def get_attendance(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user = Depends(get_current_user)
):
    """Get attendance records for a specific date (managers only)"""
    try:
        # Check if user has permission to view all attendance
        if current_user.role not in ['manager', 'admin', 'director', 'team_lead', 'sales_manager', 'dev_manager']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view team attendance"
            )
        
        # Use today's date if not provided
        if not date:
            date = get_ist_date_iso()
        
        print(f"Getting attendance for date: {date}")
        
        # Get attendance for all users on the specified date
        attendances = await DatabaseAttendance.get_attendance_by_date(date)
        
        # Convert to response format
        response_list = []
        for attendance in attendances:
            response_dict = {
                "_id": str(attendance.id),
                "user_id": str(attendance.user_id),
                "date": attendance.date,
                "check_in": attendance.check_in,
                "check_out": attendance.check_out,
                "check_in_location": attendance.check_in_location,
                "check_out_location": attendance.check_out_location,
                "check_in_note": attendance.check_in_note,
                "check_out_note": attendance.check_out_note,
                "work_summary": attendance.work_summary,
                "is_late": attendance.is_late,
                "is_complete": attendance.is_complete,
                "work_hours": attendance.work_hours,
                "status": "present" if attendance.check_in else "absent",
                "created_at": attendance.created_at,
                "updated_at": attendance.updated_at
            }
            response_list.append(AttendanceResponse(**response_dict))
        
        return response_list
        
    except Exception as e:
        print(f"Error in get_attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance: {str(e)}"
        )

@router.get("/by-date", response_model=List[AttendanceResponse])
async def get_attendance_by_date(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user = Depends(get_current_user)
):
    """Get all attendance records for a specific date (managers only)"""
    try:
        # Check if user has permission to view all attendance
        if current_user.role not in ['manager', 'admin', 'director', 'team_lead', 'sales_manager', 'dev_manager']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view team attendance"
            )
        
        print(f"Getting attendance by date: {date} for manager: {current_user.username}")
        
        # Get attendance records for the date
        attendance_records = await DatabaseAttendance.get_attendance_by_date(date)
        
        # Convert to response format
        response_list = []
        for attendance in attendance_records:
            response_dict = {
                "_id": str(attendance.id),
                "user_id": str(attendance.user_id),
                "date": attendance.date,
                "check_in": attendance.check_in,
                "check_out": attendance.check_out,
                "check_in_location": attendance.check_in_location,
                "check_out_location": attendance.check_out_location,
                "check_in_note": attendance.check_in_note,
                "check_out_note": attendance.check_out_note,
                "work_summary": attendance.work_summary,
                "is_late": attendance.is_late,
                "is_complete": attendance.is_complete,
                "work_hours": attendance.work_hours,
                "status": attendance.status,
                "created_at": attendance.created_at,
                "updated_at": attendance.updated_at
            }
            response_list.append(AttendanceResponse(**response_dict))
        
        return response_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_attendance_by_date: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance: {str(e)}"
        )

@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: str,
    update_data: dict,
    current_user = Depends(get_current_user)
):
    """Update an attendance record (managers only)"""
    try:
        print(f"Starting update_attendance for ID: {attendance_id}")
        print(f"Update data received: {update_data}")
        
        # Check if user has permission to update attendance
        if current_user.role not in ['manager', 'admin', 'director', 'team_lead', 'sales_manager', 'dev_manager', 'hr']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update attendance records"
            )
        
        print(f"User {current_user.username} has permission to update attendance")
        
        print(f"Updating attendance record: {attendance_id} by user: {current_user.username}")
        print(f"Update data: {update_data}")
        
        # Get the existing attendance record first
        print("Getting existing record...")
        existing_record = DatabaseAttendance.get_attendance_by_id(attendance_id)
        if not existing_record:
            print(f"No record found for ID: {attendance_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        print(f"Found existing record: {existing_record.id}")
        
        # Update the attendance record
        print("Calling update_attendance...")
        updated_record = DatabaseAttendance.update_attendance(attendance_id, update_data)
        
        if not updated_record:
            print("Update returned None")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update attendance record"
            )
        
        print(f"Update successful, creating response...")
        
        # Convert to AttendanceResponse format
        try:
            print("Response created successfully")
            
            # Create response with safe field access
            response_data = {
                "id": str(updated_record.id),
                "user_id": str(updated_record.user_id),
                "date": str(updated_record.date),
                "check_in": updated_record.check_in,
                "check_out": updated_record.check_out,
                "check_in_location": updated_record.check_in_location or None,
                "check_out_location": updated_record.check_out_location or None,
                "check_in_note": updated_record.check_in_note or None,
                "check_out_note": updated_record.check_out_note or None,
                "work_summary": updated_record.work_summary or None,
                "is_late": bool(updated_record.is_late),
                "is_complete": bool(updated_record.is_complete),
                "work_hours": float(updated_record.work_hours) if updated_record.work_hours else None,
                "status": str(updated_record.status),
                "created_at": updated_record.created_at,
                "updated_at": updated_record.updated_at
            }
            
            print(f"Response data prepared: {response_data}")
            
            response = AttendanceResponse(**response_data)
            print("AttendanceResponse created successfully")
            return response
        except Exception as resp_error:
            print(f"Error creating response: {resp_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create response: {str(resp_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update attendance: {str(e)}"
        )

@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: str,
    current_user = Depends(get_current_user)
):
    """Delete an attendance record (managers only)"""
    try:
        # Check if user has permission to delete attendance
        if current_user.role not in ['manager', 'admin', 'director', 'team_lead', 'sales_manager', 'dev_manager', 'hr']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete attendance records"
            )
        
        print(f"Deleting attendance record: {attendance_id} by user: {current_user.username}")
        
        # Delete the attendance record
        success = await DatabaseAttendance.delete_attendance(attendance_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        return {"message": "Attendance record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attendance: {str(e)}"
        )