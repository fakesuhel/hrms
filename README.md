from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date

from app.database.leave_requests import LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestApproval, LeaveRequestResponse, DatabaseLeaveRequests
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/leave-requests",
    tags=["leave_requests"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=LeaveRequestResponse)
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
        return LeaveRequestResponse(**leave.dict(by_alias=True))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
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
    return [LeaveRequestResponse(**leave.dict(by_alias=True)) for leave in leave_requests]

@router.get("/pending-approval", response_model=List[LeaveRequestResponse])
async def get_pending_approvals(current_user = Depends(get_current_user)):
    # Verify user has permission to approve leaves
    if current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve leave requests"
        )
    
    leave_requests = await DatabaseLeaveRequests.get_pending_approval_requests(str(current_user.id))
    return [LeaveRequestResponse(**leave.dict(by_alias=True)) for leave in leave_requests]

@router.get("/balance", response_model=dict)
async def get_leave_balance(current_user = Depends(get_current_user)):
    balance = await DatabaseLeaveRequests.get_leave_balance(str(current_user.id))
    return balance

@router.get("/{leave_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    leave_id: str,
    current_user = Depends(get_current_user)
):
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
    
    return LeaveRequestResponse(**leave.dict(by_alias=True))

@router.put("/{leave_id}", response_model=LeaveRequestResponse)
async def update_leave_request(
    leave_id: str,
    leave_data: LeaveRequestUpdate,
    current_user = Depends(get_current_user)
):
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
    return LeaveRequestResponse(**updated_leave.dict(by_alias=True))

@router.post("/{leave_id}/approve", response_model=LeaveRequestResponse)
async def approve_reject_leave(
    leave_id: str,
    approval_data: LeaveRequestApproval,
    current_user = Depends(get_current_user)
):
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
    
    # Verify user has permission to approve/reject
    if current_user.role not in ['team_lead', 'manager', 'admin']:
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
    return LeaveRequestResponse(**updated_leave.dict(by_alias=True))

@router.post("/{leave_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave_request(
    leave_id: str,
    current_user = Depends(get_current_user)
):
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
    return LeaveRequestResponse(**updated_leave.dict(by_alias=True))

# How to fix "Address already in use" error for uvicorn/FastAPI

# This error means another process is already using the port (default 8000).
# To fix:
# 1. Find the process using the port:
#    lsof -i :8000
# 2. Kill the process (replace <PID> with the actual process ID):
#    kill <PID>
#    # or force kill if needed:
#    kill -9 <PID>
# 3. Now you can restart uvicorn.

# Alternatively, run uvicorn on a different port:
#    uvicorn app.__main__:app --reload --host 0.0.0.0 --port 8001

## Backend start karne ka terminal command

```bash
source .venv/bin/activate
uvicorn app.__main__:app --reload --host 0.0.0.0 --port 8000
```

# Agar port 8000 busy hai, to dusra port use karo:
```bash
uvicorn app.__main__:app --reload --host 0.0.0.0 --port 8001
```# GitHub Activity Test - Fri Aug 22 04:03:13 PM IST 2025
