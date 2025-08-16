from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date

from app.database.performance_reviews import (
    PerformanceReviewCreate, 
    PerformanceReviewUpdate, 
    UserAcknowledgement,
    PerformanceReviewResponse, 
    DatabasePerformanceReviews
)
from app.utils.auth import get_current_user

def convert_review_to_response(review) -> dict:
    """Convert a review object to response format with proper field conversions"""
    response_data = review.dict(by_alias=True)
    response_data["_id"] = str(response_data["_id"])
    response_data["user_id"] = str(response_data["user_id"])
    response_data["reviewer_id"] = str(response_data["reviewer_id"])
    
    # Convert ratings to proper format
    if "ratings" in response_data and response_data["ratings"]:
        response_data["ratings"] = [
            {
                "category": rating.get("category", ""),
                "rating": rating.get("rating", 0.0),
                "comments": rating.get("comments")  # Allow None
            }
            for rating in response_data["ratings"]
        ]
    
    return response_data

router = APIRouter(
    prefix="/performance-reviews",
    tags=["performance_reviews"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=PerformanceReviewResponse)
async def create_performance_review(
    review_data: PerformanceReviewCreate,
    current_user = Depends(get_current_user)
):
    # Verify user has permission to create reviews
    if current_user.role not in ['team_lead', 'manager', 'dev_manager', 'sales_manager', 'hr_manager', 'admin', 'director']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create performance reviews"
        )
    
    # Verify reviewer is the current user
    if str(review_data.reviewer_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer must be the current user"
        )
    
    # Get all valid team members for this reviewer
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    # Get users from active projects and tasks where reviewer is manager
    from app.database.projects import DatabaseProjects
    project_user_ids = await DatabaseProjects.get_users_from_active_projects_and_tasks(str(current_user.id))
    
    # Combine both lists of valid users
    valid_user_ids = set(team_ids).union(set(project_user_ids))
    
    # Check if the user being reviewed is valid
    if str(review_data.user_id) not in valid_user_ids and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create reviews for users outside your team, projects, or tasks"
        )
    
    try:
        review = await DatabasePerformanceReviews.create_review(review_data)
        
        # Convert to response format
        response_data = convert_review_to_response(review)
        return PerformanceReviewResponse(**response_data)
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

@router.get("/eligible-users", response_model=List[dict])
async def get_eligible_users_for_review(
    current_user = Depends(get_current_user)
):
    """Get all users that the current user can create performance reviews for"""
    # Verify user has permission to create reviews
    if current_user.role not in ['team_lead', 'manager', 'dev_manager', 'sales_manager', 'hr_manager', 'admin', 'director']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to conduct performance reviews"
        )
    
    try:
        # Get team members from organizational hierarchy
        from app.database.users import DatabaseUsers
        team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
        team_ids = [str(member.id) for member in team_members]
        
        # Get users from active projects and tasks
        from app.database.projects import DatabaseProjects
        project_user_ids = await DatabaseProjects.get_users_from_active_projects_and_tasks(str(current_user.id))
        
        # Combine both lists of valid users
        valid_user_ids = set(team_ids).union(set(project_user_ids))
        
        # Get full user details for all eligible users
        eligible_users = []
        for user_id in valid_user_ids:
            user = await DatabaseUsers.get_user_by_id(user_id)
            if user and user.is_active:
                eligible_users.append({
                    "_id": str(user.id),
                    "id": str(user.id),
                    "username": user.username,
                    "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                    "name": user.first_name or user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "position": user.position,
                    "department": user.department,
                    "role": user.role
                })
        
        return eligible_users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get eligible users: {str(e)}"
        )

@router.get("/", response_model=List[PerformanceReviewResponse])
async def get_my_performance_reviews(current_user = Depends(get_current_user)):
    """Get all performance reviews for the current user"""
    # For managers, show all reviews they can access
    if current_user.role in ['dev_manager', 'sales_manager', 'hr_manager', 'admin', 'director']:
        reviews = await DatabasePerformanceReviews.get_all_reviews_for_manager(current_user.role)
    else:
        # For regular users, show only their own reviews
        reviews = await DatabasePerformanceReviews.get_user_reviews(str(current_user.id))
    
    response_reviews = []
    for review in reviews:
        response_data = convert_review_to_response(review)
        response_reviews.append(PerformanceReviewResponse(**response_data))
    
    return response_reviews

@router.get("/conducting", response_model=List[PerformanceReviewResponse])
async def get_reviews_conducted(
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get all reviews conducted by the current user"""
    # Verify user can conduct reviews
    if current_user.role not in ['team_lead', 'manager', 'dev_manager', 'sales_manager', 'hr_manager', 'admin', 'director']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to conduct performance reviews"
        )
    
    reviews = await DatabasePerformanceReviews.get_reviews_by_reviewer(str(current_user.id), status)
    
    response_reviews = []
    for review in reviews:
        response_data = convert_review_to_response(review)
        response_reviews.append(PerformanceReviewResponse(**response_data))
    
    return response_reviews

@router.get("/team/{review_period}", response_model=List[PerformanceReviewResponse])
async def get_team_reviews(
    review_period: str,
    current_user = Depends(get_current_user)
):
    """Get all reviews for a team in a specific period"""
    # Verify user has permission to view team reviews
    if current_user.role not in ['team_lead', 'manager', 'dev_manager', 'sales_manager', 'hr_manager', 'admin', 'director']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team reviews"
        )
    
    # Get team members from organizational hierarchy
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    # Get users from active projects and tasks
    from app.database.projects import DatabaseProjects
    project_user_ids = await DatabaseProjects.get_users_from_active_projects_and_tasks(str(current_user.id))
    
    # Combine both lists of valid users
    valid_user_ids = set(team_ids).union(set(project_user_ids))
    
    # Get reviews for all valid users
    reviews = await DatabasePerformanceReviews.get_team_reviews(list(valid_user_ids), review_period)
    
    response_reviews = []
    for review in reviews:
        response_data = convert_review_to_response(review)
        response_reviews.append(PerformanceReviewResponse(**response_data))
    
    return response_reviews

@router.get("/stats", response_model=dict)
async def get_performance_stats(
    periods: int = Query(4, ge=1, le=10),
    current_user = Depends(get_current_user)
):
    """Get performance stats for the current user"""
    stats = await DatabasePerformanceReviews.get_performance_stats(str(current_user.id), periods)
    # Add current timestamp
    stats["timestamp"] = "2025-06-10 13:24:24"
    stats["user"] = "soherucontinue"
    return stats

@router.get("/{review_id}", response_model=PerformanceReviewResponse)
async def get_review_by_id(
    review_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific performance review"""
    review = await DatabasePerformanceReviews.get_review_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user has permission to view this review
    if str(review.user_id) != str(current_user.id) and str(review.reviewer_id) != str(current_user.id) and current_user.role not in ['admin', 'dev_manager', 'sales_manager', 'hr_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this review"
        )
    
    response_data = convert_review_to_response(review)
    return PerformanceReviewResponse(**response_data)

@router.put("/{review_id}", response_model=PerformanceReviewResponse)
async def update_review(
    review_id: str,
    review_data: PerformanceReviewUpdate,
    current_user = Depends(get_current_user)
):
    """Update a performance review"""
    try:
        # Check if review exists
        review = await DatabasePerformanceReviews.get_review_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Verify user is the reviewer
        if str(review.reviewer_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the reviewer can update the review"
            )
        
        # Only allow updates to non-completed reviews
        if review.status == "completed" and review_data.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update completed reviews"
            )
        
        updated_review = await DatabasePerformanceReviews.update_review(review_id, review_data)
        
        if not updated_review:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update review"
            )
        
        response_data = convert_review_to_response(updated_review)
        return PerformanceReviewResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_review route: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{review_id}/acknowledge", response_model=PerformanceReviewResponse)
async def acknowledge_review(
    review_id: str,
    acknowledgement: UserAcknowledgement,
    current_user = Depends(get_current_user)
):
    """Employee acknowledges a performance review"""
    # Check if review exists
    review = await DatabasePerformanceReviews.get_review_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify user is the one being reviewed
    if str(review.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reviewed employee can acknowledge the review"
        )
    
    # Only allow acknowledgement of completed reviews
    if review.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only acknowledge completed reviews"
        )
    
    # Prevent re-acknowledgement
    if review.acknowledged_by_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already acknowledged"
        )
    
    acknowledged_review = await DatabasePerformanceReviews.acknowledge_review(review_id, acknowledgement)
    
    response_data = convert_review_to_response(acknowledged_review)
    return PerformanceReviewResponse(**response_data)