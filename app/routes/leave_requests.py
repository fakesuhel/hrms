from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
from datetime import date
from bson import ObjectId

from app.database.leave_requests import LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestApproval, LeaveRequestResponse, DatabaseLeaveRequests
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/leave-requests",
    tags=["leave_requests"],
    responses={404: {"description": "Not found"}},
)

def validate_leave_id(leave_id: str) -> str:
    """Validate leave_id format and return it if valid"""
    if leave_id in ["undefined", "null", ""] or not leave_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leave request ID"
        )
    
    # Validate ObjectId format
    try:
        ObjectId(leave_id)  # This will raise an exception if invalid
        return leave_id
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leave request ID format"
        )

def convert_objectids_to_strings(leave_dict):
    """Convert ObjectId fields to strings for API response"""
    if '_id' in leave_dict:
        leave_dict['_id'] = str(leave_dict['_id'])
    if 'user_id' in leave_dict:
        leave_dict['user_id'] = str(leave_dict['user_id'])
    if 'approver_id' in leave_dict and leave_dict['approver_id']:
        leave_dict['approver_id'] = str(leave_dict['approver_id'])
    
    # Convert date objects to ISO format strings
    from datetime import date, datetime
    if 'start_date' in leave_dict and isinstance(leave_dict['start_date'], date):
        leave_dict['start_date'] = leave_dict['start_date'].isoformat()
    if 'end_date' in leave_dict and isinstance(leave_dict['end_date'], date):
        leave_dict['end_date'] = leave_dict['end_date'].isoformat()
    if 'created_at' in leave_dict and isinstance(leave_dict['created_at'], datetime):
        leave_dict['created_at'] = leave_dict['created_at'].isoformat()
    if 'updated_at' in leave_dict and isinstance(leave_dict['updated_at'], datetime):
        leave_dict['updated_at'] = leave_dict['updated_at'].isoformat()
    if 'approved_at' in leave_dict and isinstance(leave_dict['approved_at'], datetime):
        leave_dict['approved_at'] = leave_dict['approved_at'].isoformat()
    
    return leave_dict

@router.post("/")
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user = Depends(get_current_user)
):
    # Verify user is requesting leave for themselves
    if str(leave_data.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot request leave for other users"
        )
    
    try:
        leave = await DatabaseLeaveRequests.create_leave_request(leave_data)
        print(f"DEBUG: Created leave record: {type(leave)}")
        
        # Convert to JSON-serializable format manually with proper datetime handling
        result = {
            "_id": str(leave.id),
            "user_id": str(leave.user_id),
            "leave_type": leave.leave_type,
            "start_date": leave.start_date.isoformat() if hasattr(leave.start_date, 'isoformat') else str(leave.start_date),
            "end_date": leave.end_date.isoformat() if hasattr(leave.end_date, 'isoformat') else str(leave.end_date),
            "reason": leave.reason,
            "contact_during_leave": leave.contact_during_leave,
            "status": leave.status,
            "approver_id": str(leave.approver_id) if leave.approver_id else None,
            "approver_comments": leave.approver_comments,
            "created_at": leave.created_at.isoformat() if hasattr(leave.created_at, 'isoformat') else str(leave.created_at),
            "updated_at": leave.updated_at.isoformat() if hasattr(leave.updated_at, 'isoformat') else str(leave.updated_at),
            "approved_at": leave.approved_at.isoformat() if leave.approved_at and hasattr(leave.approved_at, 'isoformat') else (str(leave.approved_at) if leave.approved_at else None),
            "duration_days": leave.duration_days
        }
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG: Exception during creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    leave_requests = await DatabaseLeaveRequests.get_user_leave_requests(
        str(current_user.id),
        status
    )
    
    # Convert ObjectId fields to strings for response
    result = []
    for leave in leave_requests:
        leave_dict = convert_objectids_to_strings(leave.dict(by_alias=True))
        result.append(LeaveRequestResponse(**leave_dict))
    
    return result

@router.get("/pending-approval", response_model=List[LeaveRequestResponse])
async def get_pending_approvals(current_user = Depends(get_current_user)):
    # Verify user has permission to approve leaves - only manager, dev_manager, and admin
    if current_user.role not in ['manager', 'dev_manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve leave requests"
        )
    
    leave_requests = await DatabaseLeaveRequests.get_pending_approval_requests(str(current_user.id))
    
    # Convert ObjectId fields to strings for response
    result = []
    for leave in leave_requests:
        leave_dict = convert_objectids_to_strings(leave.dict(by_alias=True))
        # Ensure we have the id field set correctly
        if '_id' in leave_dict and 'id' not in leave_dict:
            leave_dict['id'] = leave_dict['_id']
        result.append(LeaveRequestResponse(**leave_dict))
    
    return result

@router.get("/all", response_model=List[LeaveRequestResponse])
async def get_all_leaves(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user)
):
    # Only managers and dev_managers can see all leaves
    if current_user.role not in ['manager', 'dev_manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all leave requests"
        )
    
    leave_requests = await DatabaseLeaveRequests.get_all_team_leaves(str(current_user.id), status)
    
    # Convert ObjectId fields to strings for response
    result = []
    for leave in leave_requests:
        leave_dict = convert_objectids_to_strings(leave.dict(by_alias=True))
        # Ensure we have the id field set correctly
        if '_id' in leave_dict and 'id' not in leave_dict:
            leave_dict['id'] = leave_dict['_id']
        result.append(LeaveRequestResponse(**leave_dict))
    
    return result

@router.get("/balance", response_model=dict)
async def get_leave_balance(current_user = Depends(get_current_user)):
    balance = await DatabaseLeaveRequests.get_leave_balance(str(current_user.id))
    return balance

@router.get("/{leave_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    leave_id: str,
    current_user = Depends(get_current_user)
):
    # Validate leave_id format
    leave_id = validate_leave_id(leave_id)
    leave = await DatabaseLeaveRequests.get_leave_request_by_id(leave_id)
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Check if user has permission to view this request
    if str(leave.user_id) != str(current_user.id):
        # Check if user is a manager of the requester
        from app.database.users import DatabaseUsers
        team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
        team_ids = [str(member.id) for member in team_members]
        
        if str(leave.user_id) not in team_ids and current_user.role not in ['admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this leave request"
            )
    
    # Convert ObjectId fields to strings for response
    leave_dict = convert_objectids_to_strings(leave.dict(by_alias=True))
    return LeaveRequestResponse(**leave_dict)

@router.put("/{leave_id}", response_model=LeaveRequestResponse)
async def update_leave_request(
    leave_id: str,
    leave_data: LeaveRequestUpdate,
    current_user = Depends(get_current_user)
):
    # Validate leave_id format
    leave_id = validate_leave_id(leave_id)
    # Check if leave exists
    leave = await DatabaseLeaveRequests.get_leave_request_by_id(leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Only allow updates to pending requests
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update non-pending leave requests"
        )
    
    # Verify user is updating their own request
    if str(leave.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update leave requests for other users"
        )
    
    updated_leave = await DatabaseLeaveRequests.update_leave_request(leave_id, leave_data)
    
    # Convert ObjectId fields to strings for response
    leave_dict = convert_objectids_to_strings(updated_leave.dict(by_alias=True))
    return LeaveRequestResponse(**leave_dict)

@router.post("/{leave_id}/approve", response_model=LeaveRequestResponse)
async def approve_reject_leave(
    leave_id: str,
    approval_data: LeaveRequestApproval,
    current_user = Depends(get_current_user)
):
    # Validate leave_id format
    leave_id = validate_leave_id(leave_id)
    
    # Check if leave exists
    leave = await DatabaseLeaveRequests.get_leave_request_by_id(leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Only allow approval/rejection of pending requests
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only approve/reject pending leave requests"
        )
    
    # Verify user has permission to approve/reject - only manager, dev_manager, and admin
    if current_user.role not in ['manager', 'admin', 'dev_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve/reject leave requests"
        )
    
    # Verify the requesting user is under this manager
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    if str(leave.user_id) not in team_ids and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve/reject leave requests for users outside your team"
        )
    
    # Set approver ID to current user
    approval_data.approver_id = current_user.id
    
    # Process approval/rejection
    updated_leave = await DatabaseLeaveRequests.process_leave_request(leave_id, approval_data)
    
    # Convert ObjectId fields to strings for response
    leave_dict = convert_objectids_to_strings(updated_leave.dict(by_alias=True))
    return LeaveRequestResponse(**leave_dict)

@router.post("/{leave_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave_request(
    leave_id: str,
    current_user = Depends(get_current_user)
):
    # Validate leave_id format
    leave_id = validate_leave_id(leave_id)
    
    # Check if leave exists
    leave = await DatabaseLeaveRequests.get_leave_request_by_id(leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Only allow cancellation of pending requests
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending leave requests"
        )
    
    # Verify user is cancelling their own request
    if str(leave.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel leave requests for other users"
        )
    
    success = await DatabaseLeaveRequests.cancel_leave_request(leave_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel leave request"
        )
    
    updated_leave = await DatabaseLeaveRequests.get_leave_request_by_id(leave_id)
    
    # Convert ObjectId fields to strings for response
    leave_dict = convert_objectids_to_strings(updated_leave.dict(by_alias=True))
    return LeaveRequestResponse(**leave_dict)

# No code changes are needed in this file to fix the 404 error for:
# "GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1"

# Explanation:
# This request is made by Chrome DevTools or browser extensions looking for debugging or configuration files.
# It is not an error in your FastAPI code. The 404 response is correct because your API does not serve this file.
# You can safely ignore these log entries, or suppress them in your logging configuration if desired.