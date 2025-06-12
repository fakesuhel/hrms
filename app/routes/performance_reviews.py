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
    if current_user.role not in ['team_lead', 'manager', 'admin']:
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
    
    # Check if the user being reviewed is under this manager
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    if str(review_data.user_id) not in team_ids and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create reviews for users outside your team"
        )
    
    try:
        review = await DatabasePerformanceReviews.create_review(review_data)
        return PerformanceReviewResponse(**review.dict(by_alias=True))
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

@router.get("/", response_model=List[PerformanceReviewResponse])
async def get_my_performance_reviews(current_user = Depends(get_current_user)):
    """Get all performance reviews for the current user"""
    reviews = await DatabasePerformanceReviews.get_user_reviews(str(current_user.id))
    return [PerformanceReviewResponse(**review.dict(by_alias=True)) for review in reviews]

@router.get("/conducting", response_model=List[PerformanceReviewResponse])
async def get_reviews_conducted(
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get all reviews conducted by the current user"""
    # Verify user can conduct reviews
    if current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to conduct performance reviews"
        )
    
    reviews = await DatabasePerformanceReviews.get_reviews_by_reviewer(str(current_user.id), status)
    return [PerformanceReviewResponse(**review.dict(by_alias=True)) for review in reviews]

@router.get("/team/{review_period}", response_model=List[PerformanceReviewResponse])
async def get_team_reviews(
    review_period: str,
    current_user = Depends(get_current_user)
):
    """Get all reviews for a team in a specific period"""
    # Verify user has permission to view team reviews
    if current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team reviews"
        )
    
    # Get team members
    from app.database.users import DatabaseUsers
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    team_ids = [str(member.id) for member in team_members]
    
    reviews = await DatabasePerformanceReviews.get_team_reviews(team_ids, review_period)
    return [PerformanceReviewResponse(**review.dict(by_alias=True)) for review in reviews]

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
    if str(review.user_id) != str(current_user.id) and str(review.reviewer_id) != str(current_user.id) and current_user.role not in ['admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this review"
        )
    
    return PerformanceReviewResponse(**review.dict(by_alias=True))

@router.put("/{review_id}", response_model=PerformanceReviewResponse)
async def update_review(
    review_id: str,
    review_data: PerformanceReviewUpdate,
    current_user = Depends(get_current_user)
):
    """Update a performance review"""
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
    return PerformanceReviewResponse(**updated_review.dict(by_alias=True))

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
    return PerformanceReviewResponse(**acknowledged_review.dict(by_alias=True))