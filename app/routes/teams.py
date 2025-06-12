from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.database.teams import TeamCreate, TeamUpdate, TeamMember, TeamResponse, DatabaseTeams
from app.utils.auth import get_current_user
from app.utils.helpers import paginate
from bson import ObjectId

router = APIRouter(
    prefix="/teams",
    tags=["teams"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user = Depends(get_current_user)
):
    # Verify user has permission to create teams
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create teams"
        )
    
    try:
        team = await DatabaseTeams.create_team(team_data)
        # Convert ObjectIds to strings for response
        team_dict = team.dict(by_alias=True)
        team_dict["_id"] = str(team_dict["_id"])
        team_dict["lead_id"] = str(team_dict["lead_id"])
        
        # Convert ObjectId to string in members list
        for member in team_dict.get("members", []):
            if "user_id" in member and not isinstance(member["user_id"], str):
                member["user_id"] = str(member["user_id"])
                
        return team_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=dict)
async def get_all_teams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    teams = await DatabaseTeams.get_all_teams()
    
    # Convert ObjectIds to strings for each team
    team_dicts = []
    for team in teams:
        team_dict = team.dict(by_alias=True)
        team_dict["_id"] = str(team_dict["_id"])
        team_dict["lead_id"] = str(team_dict["lead_id"])
        
        # Convert ObjectId to string in members list
        for member in team_dict.get("members", []):
            if "user_id" in member and not isinstance(member["user_id"], str):
                member["user_id"] = str(member["user_id"])
        
        team_dicts.append(team_dict)
    
    return paginate(team_dicts, page, size)

@router.get("/my-teams", response_model=List[TeamResponse])
async def get_my_teams(current_user = Depends(get_current_user)):
    teams = await DatabaseTeams.get_user_teams(str(current_user.id))
    
    # Convert ObjectIds to strings for each team
    team_dicts = []
    for team in teams:
        team_dict = team.dict(by_alias=True)
        team_dict["_id"] = str(team_dict["_id"])
        team_dict["lead_id"] = str(team_dict["lead_id"])
        
        # Convert ObjectId to string in members list
        for member in team_dict.get("members", []):
            if "user_id" in member and not isinstance(member["user_id"], str):
                member["user_id"] = str(member["user_id"])
        
        team_dicts.append(team_dict)
    
    return team_dicts

@router.get("/lead", response_model=TeamResponse)
async def get_team_by_lead(current_user = Depends(get_current_user)):
    # This endpoint gets a team where the current user is the team lead
    team = await DatabaseTeams.get_team_by_lead(str(current_user.id))
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not leading any team"
        )
    
    # Convert ObjectIds to strings
    team_dict = team.dict(by_alias=True)
    team_dict["_id"] = str(team_dict["_id"])
    team_dict["lead_id"] = str(team_dict["lead_id"])
    
    # Convert ObjectId to string in members list
    for member in team_dict.get("members", []):
        if "user_id" in member and not isinstance(member["user_id"], str):
            member["user_id"] = str(member["user_id"])
        
    return team_dict

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_by_id(team_id: str, current_user = Depends(get_current_user)):
    team = await DatabaseTeams.get_team_by_id(team_id)
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Convert ObjectIds to strings
    team_dict = team.dict(by_alias=True)
    team_dict["_id"] = str(team_dict["_id"])
    team_dict["lead_id"] = str(team_dict["lead_id"])
    
    # Convert ObjectId to string in members list
    for member in team_dict.get("members", []):
        if "user_id" in member and not isinstance(member["user_id"], str):
            member["user_id"] = str(member["user_id"])
        
    return team_dict

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user = Depends(get_current_user)
):
    # Check if team exists
    team = await DatabaseTeams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Verify user has permission to update team
    if str(team.lead_id) != str(current_user.id) and current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this team"
        )
    
    updated_team = await DatabaseTeams.update_team(team_id, team_data)
    
    # Convert ObjectIds to strings
    team_dict = updated_team.dict(by_alias=True)
    team_dict["_id"] = str(team_dict["_id"])
    team_dict["lead_id"] = str(team_dict["lead_id"])
    
    # Convert ObjectId to string in members list
    for member in team_dict.get("members", []):
        if "user_id" in member and not isinstance(member["user_id"], str):
            member["user_id"] = str(member["user_id"])
        
    return team_dict

@router.post("/{team_id}/members", response_model=TeamResponse)
async def add_team_member(
    team_id: str,
    member: TeamMember,
    current_user = Depends(get_current_user)
):
    # Check if team exists
    team = await DatabaseTeams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Verify user has permission to add members
    if str(team.lead_id) != str(current_user.id) and current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add members to this team"
        )
    
    success = await DatabaseTeams.add_team_member(team_id, member)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add team member, they may already be in the team"
        )
    
    updated_team = await DatabaseTeams.get_team_by_id(team_id)
    
    # Convert ObjectIds to strings
    team_dict = updated_team.dict(by_alias=True)
    team_dict["_id"] = str(team_dict["_id"])
    team_dict["lead_id"] = str(team_dict["lead_id"])
    
    # Convert ObjectId to string in members list
    for member in team_dict.get("members", []):
        if "user_id" in member and not isinstance(member["user_id"], str):
            member["user_id"] = str(member["user_id"])
        
    return team_dict

@router.delete("/{team_id}/members/{user_id}", response_model=TeamResponse)
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user = Depends(get_current_user)
):
    # Check if team exists
    team = await DatabaseTeams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Verify user has permission to remove members
    if str(team.lead_id) != str(current_user.id) and current_user.role not in ['admin', 'manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove members from this team"
        )
    
    success = await DatabaseTeams.remove_team_member(team_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove team member"
        )
    
    updated_team = await DatabaseTeams.get_team_by_id(team_id)
    
    # Convert ObjectIds to strings
    team_dict = updated_team.dict(by_alias=True)
    team_dict["_id"] = str(team_dict["_id"])
    team_dict["lead_id"] = str(team_dict["lead_id"])
    
    # Convert ObjectId to string in members list
    for member in team_dict.get("members", []):
        if "user_id" in member and not isinstance(member["user_id"], str):
            member["user_id"] = str(member["user_id"])
        
    return team_dict