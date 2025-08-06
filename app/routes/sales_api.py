"""
Sales API Routes for HRMS System
Provides endpoints for leads, customers, and sales statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.utils.auth import get_current_user
from app.database.users import UserInDB
from app.database import (
    leads_collection, customers_collection, 
    projects_collection, users_collection
)
from bson import ObjectId
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now()

def is_sales_user(user: UserInDB) -> bool:
    """Check if user has sales access"""
    # Check if user is in sales department
    if user.department and user.department.lower() == 'sales':
        return True
    
    # Check if user has sales position
    if user.position in ['sales_manager', 'sales_executive']:
        return True
    
    # Check if user has admin/director role
    if user.role in ['admin', 'director']:
        return True
    
    return False

def is_sales_manager(user: UserInDB) -> bool:
    """Check if user is a sales manager"""
    # Check role
    if user.role in ['admin', 'director', 'manager']:
        return True
    
    # Check position
    if user.position == 'sales_manager':
        return True
    
    # Check if user is in sales department and has manager role
    if user.department and user.department.lower() == 'sales' and user.role == 'manager':
        return True
    
    return False

router = APIRouter(prefix="/api/sales", tags=["sales"])

def serialize_object_id(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_object_id(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

@router.post("/sample-data")
async def create_sample_data(current_user: UserInDB = Depends(get_current_user)):
    """Create sample leads and customers for testing (admin only)"""
    try:
        if current_user.role not in ['admin', 'director', 'sales_manager']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and sales managers can create sample data"
            )
        
        # Sample leads data
        sample_leads = [
            {
                "company_name": "TechCorp Solutions",
                "contact_person": "John Smith",
                "email": "john.smith@techcorp.com",
                "phone": "+1-555-0101",
                "status": "new",
                "deal_value": 50000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Interested in enterprise software solution"
            },
            {
                "company_name": "Global Industries",
                "contact_person": "Sarah Johnson", 
                "email": "sarah.j@globalind.com",
                "phone": "+1-555-0102",
                "status": "contacted",
                "deal_value": 75000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Had initial call, needs proposal"
            },
            {
                "company_name": "Startup Innovations",
                "contact_person": "Mike Wilson",
                "email": "mike@startupinov.com",
                "phone": "+1-555-0103", 
                "status": "qualified",
                "deal_value": 25000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Qualified lead, ready for proposal"
            },
            {
                "company_name": "Enterprise Corp",
                "contact_person": "Lisa Brown",
                "email": "lisa.brown@enterprise.com",
                "phone": "+1-555-0104",
                "status": "proposal", 
                "deal_value": 100000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Proposal sent, awaiting response"
            },
            {
                "company_name": "Success Company",
                "contact_person": "David Lee",
                "email": "david.lee@success.com",
                "phone": "+1-555-0105",
                "status": "closed_won",
                "deal_value": 80000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Deal closed successfully",
                "payment_milestones": [
                    {
                        "id": str(ObjectId()),
                        "description": "Initial Payment (50%)",
                        "amount": 40000,
                        "due_date": "2025-08-01",
                        "status": "paid",
                        "created_at": get_ist_now().isoformat(),
                        "created_by": current_user.username,
                        "paid_date": "2025-07-20"
                    },
                    {
                        "id": str(ObjectId()),
                        "description": "Final Payment (50%)",
                        "amount": 40000,
                        "due_date": "2025-09-01", 
                        "status": "paid",
                        "created_at": get_ist_now().isoformat(),
                        "created_by": current_user.username,
                        "paid_date": "2025-07-20"
                    }
                ],
                "payment_tracking": {
                    "total_amount": 80000,
                    "paid_amount": 80000,
                    "remaining_amount": 0,
                    "payments": [
                        {
                            "id": str(ObjectId()),
                            "amount": 40000,
                            "payment_method": "Bank Transfer",
                            "payment_date": "2025-07-20",
                            "transaction_id": "TXN001",
                            "notes": "Initial payment received",
                            "recorded_at": get_ist_now().isoformat(),
                            "recorded_by": current_user.username
                        },
                        {
                            "id": str(ObjectId()),
                            "amount": 40000,
                            "payment_method": "Bank Transfer", 
                            "payment_date": "2025-07-20",
                            "transaction_id": "TXN002",
                            "notes": "Final payment received",
                            "recorded_at": get_ist_now().isoformat(),
                            "recorded_by": current_user.username
                        }
                    ]
                }
            }
        ]
        
        # Sample customers data
        sample_customers = [
            {
                "company_name": "Existing Client A",
                "contact_person": "Robert Taylor",
                "email": "robert@clienta.com",
                "phone": "+1-555-0201",
                "status": "active",
                "customer_value": 120000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Long-term customer, very satisfied"
            },
            {
                "company_name": "Loyal Customer B",
                "contact_person": "Emily Davis",
                "email": "emily@customerb.com", 
                "phone": "+1-555-0202",
                "status": "active",
                "customer_value": 95000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Regular customer, potential for upsell"
            },
            {
                "company_name": "Premium Client C",
                "contact_person": "James Anderson",
                "email": "james@premiumc.com",
                "phone": "+1-555-0203",
                "status": "active", 
                "customer_value": 150000,
                "assigned_to": "sales_emp",
                "created_by": current_user.username,
                "created_at": get_ist_now().isoformat(),
                "updated_at": get_ist_now().isoformat(),
                "notes": "Premium tier customer, excellent relationship"
            }
        ]
        
        # Insert sample data
        leads_result = leads_collection.insert_many(sample_leads)
        customers_result = customers_collection.insert_many(sample_customers)
        
        return {
            "message": "Sample data created successfully",
            "leads_created": len(leads_result.inserted_ids),
            "customers_created": len(customers_result.inserted_ids)
        }
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample data: {str(e)}"
        )

@router.get("/leads")
async def get_leads(
    current_user: UserInDB = Depends(get_current_user),
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100
):
    """Get leads with optional filtering"""
    try:
        # Build query filter
        query = {}
        
        # Role-based filtering
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager', 'team_lead']:
            # Non-managers can only see their own leads
            query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        # Additional filters
        if status:
            query["status"] = status
        if assigned_to:
            query["assigned_to"] = assigned_to
            
        # Get leads from database
        leads_cursor = leads_collection.find(query).limit(limit)
        leads = []
        
        for lead in leads_cursor:
            # Convert ObjectId to string and ensure required fields
            lead_data = serialize_object_id(lead)
            
            # Ensure required fields exist
            lead_data.setdefault("company_name", lead_data.get("company", "Unknown Company"))
            lead_data.setdefault("contact_person", lead_data.get("contact_name", "Unknown Contact"))
            lead_data.setdefault("deal_value", lead_data.get("value", 0))
            lead_data.setdefault("status", "new")
            lead_data.setdefault("assigned_to", current_user.username)
            lead_data.setdefault("created_by", current_user.username)
            lead_data.setdefault("created_at", get_ist_now().isoformat())
            lead_data.setdefault("updated_at", get_ist_now().isoformat())
            
            leads.append(lead_data)
        
        logger.info(f"Retrieved {len(leads)} leads for user {current_user.username}")
        return leads
        
    except Exception as e:
        logger.error(f"Error retrieving leads: {str(e)}")
        # Return empty list instead of error to prevent dashboard breaking
        return []

@router.get("/customers")
async def get_customers(
    current_user: UserInDB = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 100
):
    """Get customers with optional filtering"""
    try:
        # Build query filter
        query = {}
        
        # Role-based filtering
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager', 'team_lead']:
            # Non-managers can only see their own customers
            query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        if status:
            query["status"] = status
            
        # Get customers from database
        customers_cursor = customers_collection.find(query).limit(limit)
        customers = []
        
        for customer in customers_cursor:
            # Convert ObjectId to string and ensure required fields
            customer_data = serialize_object_id(customer)
            
            # Ensure required fields exist
            customer_data.setdefault("company_name", customer_data.get("company", "Unknown Company"))
            customer_data.setdefault("contact_person", customer_data.get("contact_name", "Unknown Contact"))
            customer_data.setdefault("customer_value", customer_data.get("value", 0))
            customer_data.setdefault("status", "active")
            customer_data.setdefault("assigned_to", current_user.username)
            customer_data.setdefault("created_by", current_user.username)
            customer_data.setdefault("created_at", get_ist_now().isoformat())
            customer_data.setdefault("updated_at", get_ist_now().isoformat())
            
            customers.append(customer_data)
        
        logger.info(f"Retrieved {len(customers)} customers for user {current_user.username}")
        return customers
        
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        # Return empty list instead of error
        return []

@router.post("/customers")
async def create_customer(
    customer_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new customer manually"""
    try:
        # Validate required fields
        if not customer_data.get("contact_person"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact person name is required"
            )
        
        if not customer_data.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required"
            )
        
        # Check if customer already exists with this phone number
        existing_customer = customers_collection.find_one({"phone": customer_data["phone"]})
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this phone number already exists"
            )
        
        # Set defaults for optional fields
        customer_data.setdefault("company_name", f"{customer_data['contact_person']}'s Company")
        customer_data.setdefault("email", "")
        customer_data.setdefault("customer_value", 0)
        customer_data.setdefault("status", "active")
        customer_data.setdefault("notes", "")
        
        # Add metadata
        customer_data.update({
            "created_by": current_user.username,
            "assigned_to": customer_data.get("assigned_to", current_user.username),
            "created_at": get_ist_now(),
            "updated_at": get_ist_now()
        })
        
        # Insert into database
        result = customers_collection.insert_one(customer_data)
        
        # Return created customer with ID
        customer_data["_id"] = str(result.inserted_id)
        return serialize_object_id(customer_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )

@router.get("/stats/leads")
async def get_leads_stats(current_user: UserInDB = Depends(get_current_user)):
    """Get leads statistics"""
    try:
        # Build base query for role-based access
        base_query = {}
        if current_user.role not in ['manager', 'admin', 'director']:
            base_query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        # Aggregate statistics
        pipeline = [
            {"$match": base_query},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_value": {"$sum": {"$ifNull": ["$deal_value", "$value", 0]}}
                }
            }
        ]
        
        # Execute aggregation
        stats_cursor = leads_collection.aggregate(pipeline)
        status_stats = {}
        status_values = {}
        total_leads = 0
        total_value = 0
        
        for stat in stats_cursor:
            status = stat["_id"] or "new"
            count = stat["count"]
            value = stat["total_value"]
            
            status_stats[status] = count
            status_values[status] = value
            total_leads += count
            total_value += value
        
        # Calculate additional metrics
        stats = {
            "total_leads": total_leads,
            "new": status_stats.get("new", 0),
            "contacted": status_stats.get("contacted", 0),
            "qualified": status_stats.get("qualified", 0),
            "proposal": status_stats.get("proposal", 0),
            "closed_won": status_stats.get("closed_won", 0),
            "closed_lost": status_stats.get("closed_lost", 0),
            "total_value": total_value,
            "won_value": status_values.get("closed_won", 0)  # Actual sum of closed_won deal values
        }
        
        logger.info(f"Generated leads stats for user {current_user.username}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating leads stats: {str(e)}")
        # Return default stats
        return {
            "total_leads": 0,
            "new": 0,
            "contacted": 0,
            "qualified": 0,
            "proposal": 0,
            "closed_won": 0,
            "closed_lost": 0,
            "total_value": 0,
            "won_value": 0
        }

@router.get("/stats/customers")
async def get_customers_stats(current_user: UserInDB = Depends(get_current_user)):
    """Get customers statistics"""
    try:
        # Build base query for role-based access
        base_query = {}
        if current_user.role not in ['manager', 'admin', 'director']:
            base_query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        # Get total customer count and value
        total_customers = customers_collection.count_documents(base_query)
        
        # Aggregate customer value
        pipeline = [
            {"$match": base_query},
            {
                "$group": {
                    "_id": None,
                    "total_value": {"$sum": {"$ifNull": ["$customer_value", "$value", 0]}},
                    "active_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "active"]},
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]
        
        stats_cursor = customers_collection.aggregate(pipeline)
        aggregated_stats = list(stats_cursor)
        
        if aggregated_stats:
            stats = aggregated_stats[0]
            return {
                "total_customers": total_customers,
                "active_customers": stats.get("active_count", 0),
                "total_value": stats.get("total_value", 0),
                "average_value": stats.get("total_value", 0) / max(total_customers, 1)
            }
        else:
            return {
                "total_customers": 0,
                "active_customers": 0,
                "total_value": 0,
                "average_value": 0
            }
        
    except Exception as e:
        logger.error(f"Error generating customers stats: {str(e)}")
        return {
            "total_customers": 0,
            "active_customers": 0,
            "total_value": 0,
            "average_value": 0
        }

@router.post("/leads")
async def create_lead(
    lead_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new lead - only person name and phone number required"""
    try:
        # Validate required fields
        if not lead_data.get("contact_person"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact person name is required"
            )
        
        if not lead_data.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required"
            )
        
        # Check if there's an existing customer with this phone number
        existing_customer = customers_collection.find_one({"phone": lead_data["phone"]})
        if existing_customer:
            # Link to existing customer
            lead_data["linked_customer_id"] = str(existing_customer["_id"])
            lead_data["company_name"] = existing_customer.get("company_name", lead_data.get("company_name", ""))
        
        # Set defaults for optional fields
        lead_data.setdefault("company_name", f"{lead_data['contact_person']}'s Company")
        lead_data.setdefault("email", "")
        lead_data.setdefault("deal_value", 0)
        lead_data.setdefault("status", "new")
        lead_data.setdefault("notes", "")
        
        # Initialize payment tracking
        lead_data.setdefault("payment_milestones", [])
        lead_data.setdefault("payment_tracking", {
            "total_amount": lead_data.get("deal_value", 0),
            "paid_amount": 0,
            "remaining_amount": lead_data.get("deal_value", 0),
            "payments": []  # List of payment records
        })
        
        # Add metadata
        lead_data.update({
            "created_by": current_user.username,
            "assigned_to": lead_data.get("assigned_to", current_user.username),
            "created_at": get_ist_now(),
            "updated_at": get_ist_now()
        })
        
        # Insert into database
        result = leads_collection.insert_one(lead_data)
        
        # Return created lead with ID
        lead_data["_id"] = str(result.inserted_id)
        return serialize_object_id(lead_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead"
        )

@router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Update an existing lead and auto-convert to customer/project if closed_won"""
    try:
        # Build query with permission check
        query = {"_id": ObjectId(lead_id)}
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager']:
            query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        # Get the existing lead first
        existing_lead = leads_collection.find_one(query)
        if not existing_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or insufficient permissions"
            )
        
        # Add update metadata
        lead_data["updated_at"] = get_ist_now()
        lead_data["updated_by"] = current_user.username
        
        # Check if lead is being marked as closed_won
        new_status = lead_data.get("status")
        old_status = existing_lead.get("status")
        
        if new_status == "closed_won" and old_status != "closed_won":
            # Auto-convert lead to customer and project
            convert_lead_to_customer_and_project(existing_lead, lead_data, current_user)
        
        # Update lead
        result = leads_collection.update_one(
            query,
            {"$set": lead_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or insufficient permissions"
            )
        
        return {"message": "Lead updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead"
        )

def convert_lead_to_customer_and_project(lead, lead_updates, current_user):
    """Convert a closed_won lead to customer and create a project"""
    try:
        phone = lead.get("phone")
        
        # Check if customer already exists with this phone number
        existing_customer = customers_collection.find_one({"phone": phone})
        
        customer_id = None
        if existing_customer:
            # Update existing customer value
            new_value = existing_customer.get("customer_value", 0) + lead.get("deal_value", 0)
            customers_collection.update_one(
                {"_id": existing_customer["_id"]},
                {"$set": {
                    "customer_value": new_value,
                    "updated_at": get_ist_now(),
                    "updated_by": current_user.username
                }}
            )
            customer_id = existing_customer["_id"]
            logger.info(f"Updated existing customer {customer_id} with additional value: {lead.get('deal_value', 0)}")
        else:
            # Create new customer
            customer_data = {
                "company_name": lead.get("company_name", f"{lead.get('contact_person', 'Unknown')}'s Company"),
                "contact_person": lead.get("contact_person"),
                "email": lead.get("email", ""),
                "phone": phone,
                "status": "active",
                "customer_value": lead.get("deal_value", 0),
                "assigned_to": lead.get("assigned_to", current_user.username),
                "created_by": current_user.username,
                "created_at": get_ist_now(),
                "updated_at": get_ist_now(),
                "notes": f"Converted from lead: {lead.get('notes', '')}"
            }
            
            customer_result = customers_collection.insert_one(customer_data)
            customer_id = customer_result.inserted_id
            logger.info(f"Created new customer {customer_id} from lead conversion")
        
        # Create project from the lead
        project_data = {
            "name": lead_updates.get("project_name", f"{lead.get('company_name', 'Client')} - {lead.get('contact_person', 'Project')}"),
            "description": lead_updates.get("requirements", lead.get("notes", "Requirements to be defined")),
            "client": lead.get("contact_person"),
            "start_date": lead_updates.get("start_date", (get_ist_now() + timedelta(days=7)).date().isoformat()),
            "end_date": lead_updates.get("due_date", (get_ist_now() + timedelta(days=90)).date().isoformat()),
            "status": "active",
            "manager_id": None,  # Will be assigned by development manager
            "team_members": [],
            "tasks": [],
            "budget": lead.get("deal_value", 0),
            "technologies": lead_updates.get("technologies", []),
            
            # Additional sales-related fields for reference
            "client_company": lead.get("company_name", f"{lead.get('contact_person', 'Unknown')}'s Company"),
            "client_email": lead.get("email", ""),
            "client_phone": lead.get("phone"),
            "customer_id": str(customer_id),
            "lead_id": str(lead["_id"]),
            "project_value": lead.get("deal_value", 0),  # For sales tracking
            "priority": "medium",
            
            "created_at": get_ist_now(),
            "updated_at": get_ist_now(),
            "created_by_sales": current_user.username,  # Track who from sales created it
            "notes": f"Auto-created from sales lead. Original lead notes: {lead.get('notes', '')}"
        }
        
        project_result = projects_collection.insert_one(project_data)
        project_id = project_result.inserted_id
        
        # Update lead with customer and project references
        leads_collection.update_one(
            {"_id": lead["_id"]},
            {"$set": {
                "linked_customer_id": str(customer_id),
                "linked_project_id": str(project_id),
                "conversion_date": get_ist_now()
            }}
        )
        
        logger.info(f"Successfully converted lead {lead['_id']} to customer {customer_id} and project {project_id}")
        
    except Exception as e:
        logger.error(f"Error in lead conversion: {str(e)}")
        # Don't raise here as this is a background process

@router.post("/leads/{lead_id}/convert")
async def manually_convert_lead(
    lead_id: str,
    conversion_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Manually convert a lead to customer and project"""
    try:
        # Get the lead
        query = {"_id": ObjectId(lead_id)}
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager']:
            query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        lead = leads_collection.find_one(query)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or insufficient permissions"
            )
        
        # Convert to customer and project
        convert_lead_to_customer_and_project(lead, conversion_data, current_user)
        
        # Update lead status to closed_won
        leads_collection.update_one(
            {"_id": ObjectId(lead_id)},
            {"$set": {
                "status": "closed_won",
                "updated_at": get_ist_now(),
                "updated_by": current_user.username
            }}
        )
        
        return {"message": "Lead converted to customer and project successfully"}
        
    except Exception as e:
        logger.error(f"Error manually converting lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert lead"
        )

@router.get("/projects")
async def get_sales_projects(
    current_user: UserInDB = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 100
):
    """Get projects - dev_manager, HR, admin, director can view all projects"""
    try:
        # Build query filter
        query = {}
        
        # Role-based filtering - These roles can view ALL projects
        privileged_roles = ['admin', 'director', 'sales_manager', 'dev_manager', 'manager']
        privileged_departments = ['Human Resources']
        
        can_view_all = (
            current_user.role in privileged_roles or 
            current_user.department in privileged_departments
        )
        
        if not can_view_all:
            # Regular employees can only see projects they are involved with
            query["$or"] = [
                {"created_by_sales": current_user.username},
                {"manager_id": current_user.username},
                {"team_members": current_user.username}
            ]
        
        if status:
            query["status"] = status
            
        # Get projects from database
        projects_cursor = projects_collection.find(query).limit(limit)
        projects = []
        
        for project in projects_cursor:
            # Convert ObjectId to string and adapt to sales view
            project_data = serialize_object_id(project)
            
            # Map development schema to sales-friendly format for compatibility
            project_data["project_name"] = project_data.get("name", "Unnamed Project")
            project_data["client_name"] = project_data.get("client", "Unknown Client")
            project_data["start_date"] = project_data.get("start_date")
            project_data["due_date"] = project_data.get("end_date")
            project_data["requirements"] = project_data.get("description", "")
            
            projects.append(project_data)
        
        logger.info(f"Retrieved {len(projects)} projects for user {current_user.username} (role: {current_user.role}, department: {getattr(current_user, 'department', 'N/A')}, can_view_all: {can_view_all})")
        return projects
        
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        return []

@router.get("/conversion-stats")
async def get_conversion_stats(current_user: UserInDB = Depends(get_current_user)):
    """Get lead conversion statistics"""
    try:
        # Build base query for role-based access
        base_query = {}
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager']:
            base_query["$or"] = [
                {"assigned_to": current_user.username},
                {"created_by": current_user.username}
            ]
        
        # Count converted leads
        converted_leads = leads_collection.count_documents({
            **base_query,
            "status": "closed_won",
            "linked_customer_id": {"$exists": True}
        })
        
        # Count total leads
        total_leads = leads_collection.count_documents(base_query)
        
        # Count projects created from leads
        projects_query = {"lead_id": {"$exists": True}}
        if current_user.role not in ['manager', 'admin', 'director', 'sales_manager']:
            projects_query["created_by"] = current_user.username
            
        projects_created = projects_collection.count_documents(projects_query)
        
        # Calculate conversion rate
        conversion_rate = (converted_leads / max(total_leads, 1)) * 100
        
        return {
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "projects_created": projects_created,
            "conversion_rate": round(conversion_rate, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversion stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversion stats: {str(e)}"
        )

@router.post("/leads/{lead_id}/payment-milestones")
async def add_payment_milestone(
    lead_id: str,
    milestone_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Add a payment milestone to a lead"""
    try:
        # Validate lead exists
        lead = leads_collection.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Check permissions - sales team access for payment milestones
        if current_user.role in ['admin', 'director', 'sales_manager', 'manager']:
            # Full access for these roles
            pass
        elif current_user.role == 'sales_executive':
            # Sales executives can only modify their own leads
            if lead.get("assigned_to") != current_user.username and \
               lead.get("created_by") != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this lead"
                )
        else:
            # Other roles have no access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this lead"
            )
        
        # Validate milestone data
        required_fields = ["description", "amount", "due_date"]
        for field in required_fields:
            if field not in milestone_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create milestone
        milestone = {
            "id": str(ObjectId()),
            "description": milestone_data["description"],
            "amount": float(milestone_data["amount"]),
            "due_date": milestone_data["due_date"],
            "status": "pending",  # pending, paid, overdue
            "created_at": get_ist_now().isoformat(),
            "created_by": current_user.username
        }
        
        # Add to lead
        leads_collection.update_one(
            {"_id": ObjectId(lead_id)},
            {
                "$push": {"payment_milestones": milestone},
                "$set": {"updated_at": get_ist_now()}
            }
        )
        
        return {"message": "Payment milestone added successfully", "milestone": milestone}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment milestone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add payment milestone: {str(e)}"
        )

@router.post("/leads/{lead_id}/payments")
async def record_payment(
    lead_id: str,
    payment_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user)
):
    """Record a payment for a lead"""
    try:
        # Validate lead exists
        lead = leads_collection.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Check permissions - sales team access for payment recording
        if current_user.role in ['admin', 'director', 'sales_manager', 'manager']:
            # Full access for these roles
            pass
        elif current_user.role == 'sales_executive':
            # Sales executives can only modify their own leads
            if lead.get("assigned_to") != current_user.username and \
               lead.get("created_by") != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this lead"
                )
        else:
            # Other roles have no access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this lead"
            )
        
        # Validate payment data
        required_fields = ["amount", "payment_method", "payment_date"]
        for field in required_fields:
            if field not in payment_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        amount = float(payment_data["amount"])
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than 0"
            )
        
        # Create payment record
        payment = {
            "id": str(ObjectId()),
            "amount": amount,
            "payment_method": payment_data["payment_method"],
            "payment_date": payment_data["payment_date"],
            "transaction_id": payment_data.get("transaction_id", ""),
            "notes": payment_data.get("notes", ""),
            "recorded_at": get_ist_now().isoformat(),
            "recorded_by": current_user.username
        }
        
        # Update payment tracking
        current_tracking = lead.get("payment_tracking", {
            "total_amount": lead.get("deal_value", 0),
            "paid_amount": 0,
            "remaining_amount": lead.get("deal_value", 0),
            "payments": []
        })
        
        new_paid_amount = current_tracking.get("paid_amount", 0) + amount
        total_amount = current_tracking.get("total_amount", lead.get("deal_value", 0))
        new_remaining_amount = max(0, total_amount - new_paid_amount)
        
        # Update milestone status if applicable
        milestone_id = payment_data.get("milestone_id")
        update_operations = {
            "$push": {"payment_tracking.payments": payment},
            "$set": {
                "payment_tracking.paid_amount": new_paid_amount,
                "payment_tracking.remaining_amount": new_remaining_amount,
                "updated_at": get_ist_now()
            }
        }
        
        if milestone_id:
            update_operations["$set"]["payment_milestones.$[milestone].status"] = "paid"
            update_operations["$set"]["payment_milestones.$[milestone].paid_date"] = payment_data["payment_date"]
            
            # Update with array filter
            leads_collection.update_one(
                {"_id": ObjectId(lead_id)},
                update_operations,
                array_filters=[{"milestone.id": milestone_id}]
            )
        else:
            leads_collection.update_one(
                {"_id": ObjectId(lead_id)},
                update_operations
            )
        
        # Check if fully paid and update lead status
        if new_remaining_amount == 0 and lead.get("status") != "closed_won":
            leads_collection.update_one(
                {"_id": ObjectId(lead_id)},
                {"$set": {"status": "closed_won", "updated_at": get_ist_now()}}
            )
        
        return {
            "message": "Payment recorded successfully",
            "payment": payment,
            "payment_summary": {
                "total_amount": total_amount,
                "paid_amount": new_paid_amount,
                "remaining_amount": new_remaining_amount,
                "payment_percentage": round((new_paid_amount / max(total_amount, 1)) * 100, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record payment: {str(e)}"
        )

@router.get("/leads/{lead_id}/payment-summary")
async def get_payment_summary(
    lead_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get payment summary for a lead"""
    try:
        # Validate lead exists
        lead = leads_collection.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Check permissions - sales team access
        if current_user.role in ['admin', 'director', 'sales_manager', 'manager']:
            # Full access for these roles
            pass
        elif current_user.role == 'sales_executive':
            # Sales executives can only view their own leads
            if lead.get("assigned_to") != current_user.username and \
               lead.get("created_by") != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this lead"
                )
        else:
            # Other roles have no access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this lead"
            )
        
        payment_tracking = lead.get("payment_tracking", {})
        milestones = lead.get("payment_milestones", [])
        
        total_amount = payment_tracking.get("total_amount", lead.get("deal_value", 0))
        paid_amount = payment_tracking.get("paid_amount", 0)
        remaining_amount = payment_tracking.get("remaining_amount", total_amount)
        
        return {
            "lead_id": lead_id,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
            "payment_percentage": round((paid_amount / max(total_amount, 1)) * 100, 2),
            "milestones": serialize_object_id(milestones),
            "payments": serialize_object_id(payment_tracking.get("payments", [])),
            "status": lead.get("status", "new")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment summary: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Error getting conversion stats: {str(e)}")
        return {
            "total_leads": 0,
            "converted_leads": 0,
            "projects_created": 0,
            "conversion_rate": 0
        }

@router.get("/reports")
async def get_sales_reports(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    team_member: Optional[str] = Query(None, description="Filter by specific team member ID"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get comprehensive sales reports with analytics and performance metrics"""
    try:
        # Check permissions - Allow sales department users and admin/director
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Build query filters
        date_filter = {
            "created_at": {
                "$gte": start_dt,
                "$lt": end_dt
            }
        }
        
        # Role-based access control - IMPROVED
        if not is_sales_manager(current_user):
            # Non-managers (sales executives) can only see their own data
            date_filter["$or"] = [
                {"assigned_to": str(current_user.id)},
                {"assigned_to": current_user.username}
            ]
            logger.info(f"Sales executive {current_user.username} viewing own reports only")
        elif team_member and is_sales_manager(current_user):
            # Sales managers can filter by team member
            date_filter["assigned_to"] = team_member
            logger.info(f"Sales manager {current_user.username} viewing reports for member: {team_member}")
        else:
            # Sales managers without filter see all team data
            logger.info(f"Sales manager {current_user.username} viewing all team reports")
        
        # Get leads data
        leads_cursor = leads_collection.find(date_filter)
        leads_data = list(leads_cursor)
        
        # Get previous period data for comparison
        prev_start = start_dt - (end_dt - start_dt)
        prev_end = start_dt
        prev_filter = {
            "created_at": {
                "$gte": prev_start,
                "$lt": prev_end
            }
        }
        
        if not is_sales_manager(current_user):
            # Non-managers see only their own previous data
            prev_filter["$or"] = [
                {"assigned_to": str(current_user.id)},
                {"assigned_to": current_user.username}
            ]
        elif team_member and is_sales_manager(current_user):
            prev_filter["assigned_to"] = team_member
            
        prev_leads_cursor = leads_collection.find(prev_filter)
        prev_leads_data = list(prev_leads_cursor)
        
        # Calculate current period metrics
        total_leads = len(leads_data)
        converted_leads = len([l for l in leads_data if l.get('status') == 'closed_won'])
        total_revenue = sum(l.get('deal_value', 0) for l in leads_data if l.get('status') == 'closed_won')
        win_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        avg_deal_size = (total_revenue / converted_leads) if converted_leads > 0 else 0
        
        # Calculate payment metrics
        payment_collected = 0
        for lead in leads_data:
            if lead.get('status') == 'closed_won' and lead.get('payment_tracking'):
                payment_collected += lead['payment_tracking'].get('paid_amount', 0)
        
        # Calculate previous period metrics for comparison
        prev_total_leads = len(prev_leads_data)
        prev_converted_leads = len([l for l in prev_leads_data if l.get('status') == 'closed_won'])
        prev_total_revenue = sum(l.get('deal_value', 0) for l in prev_leads_data if l.get('status') == 'closed_won')
        prev_win_rate = (prev_converted_leads / prev_total_leads * 100) if prev_total_leads > 0 else 0
        prev_avg_deal_size = (prev_total_revenue / prev_converted_leads) if prev_converted_leads > 0 else 0
        
        prev_payment_collected = 0
        for lead in prev_leads_data:
            if lead.get('status') == 'closed_won' and lead.get('payment_tracking'):
                prev_payment_collected += lead['payment_tracking'].get('paid_amount', 0)
        
        # Calculate percentage changes
        def calculate_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100
        
        # Lead status distribution
        status_distribution = defaultdict(int)
        for lead in leads_data:
            status_distribution[lead.get('status', 'unknown')] += 1
        
        # Performance trend (monthly breakdown)
        performance_trend = []
        current_date = start_dt
        while current_date < end_dt - timedelta(days=1):
            month_end = min(current_date + timedelta(days=30), end_dt - timedelta(days=1))
            month_leads = [l for l in leads_data if current_date <= l.get('created_at', datetime.min) < month_end]
            month_conversions = [l for l in month_leads if l.get('status') == 'closed_won']
            
            performance_trend.append({
                "month": current_date.strftime("%b %Y"),
                "leads": len(month_leads),
                "conversions": len(month_conversions)
            })
            current_date = month_end
        
        # Payment trend
        payment_trend = []
        current_date = start_dt
        while current_date < end_dt - timedelta(days=1):
            month_end = min(current_date + timedelta(days=30), end_dt - timedelta(days=1))
            month_leads = [l for l in leads_data if current_date <= l.get('created_at', datetime.min) < month_end]
            
            expected = sum(l.get('deal_value', 0) for l in month_leads if l.get('status') == 'closed_won')
            collected = sum(l.get('payment_tracking', {}).get('paid_amount', 0) for l in month_leads if l.get('status') == 'closed_won')
            
            payment_trend.append({
                "month": current_date.strftime("%b %Y"),
                "expected": expected,
                "collected": collected
            })
            current_date = month_end
        
        # Win rate by source
        source_stats = defaultdict(lambda: {"total": 0, "won": 0})
        for lead in leads_data:
            source = lead.get('source', 'unknown')
            source_stats[source]["total"] += 1
            if lead.get('status') == 'closed_won':
                source_stats[source]["won"] += 1
        
        win_rate_by_source = {}
        for source, stats in source_stats.items():
            win_rate_by_source[source] = (stats["won"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        return {
            "overview": {
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "total_revenue": total_revenue,
                "win_rate": win_rate,
                "avg_deal_size": avg_deal_size,
                "payment_collected": payment_collected,
                "team_performance": win_rate,  # Use win_rate as team performance metric
                "leads_change": calculate_change(total_leads, prev_total_leads),
                "conversion_change": calculate_change(converted_leads, prev_converted_leads),
                "revenue_change": calculate_change(total_revenue, prev_total_revenue),
                "win_rate_change": calculate_change(win_rate, prev_win_rate),
                "deal_size_change": calculate_change(avg_deal_size, prev_avg_deal_size),
                "payment_change": calculate_change(payment_collected, prev_payment_collected),
                "team_performance_change": calculate_change(win_rate, prev_win_rate)
            },
            "lead_status_distribution": dict(status_distribution),
            "performance_trend": performance_trend,
            "payment_trend": payment_trend,
            "win_rate_by_source": win_rate_by_source,
            "trends": {
                "labels": [trend["month"] for trend in performance_trend],
                "revenue": [sum(l.get('deal_value', 0) for l in leads_data 
                           if l.get('created_at', datetime.min).strftime("%b %Y") == trend["month"] 
                           and l.get('status') == 'closed_won') for trend in performance_trend],
                "leads": [trend["leads"] for trend in performance_trend]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating sales reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reports: {str(e)}"
        )

@router.get("/team-performance")
async def get_team_performance(current_user: UserInDB = Depends(get_current_user)):
    """Get team performance data (sales managers only)"""
    try:
        # Check permissions - only sales managers can view team performance
        if current_user.position != 'sales_manager' and current_user.role not in ['admin', 'director']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales manager access required."
            )
        
        # Get all sales team members
        team_members_cursor = users_collection.find({
            "position": {"$in": ["sales_executive", "sales_manager"]},
            "is_active": True
        })
        team_members = list(team_members_cursor)
        
        team_performance = []
        
        for member in team_members:
            member_id = str(member["_id"])
            
            # Get member's leads
            member_leads = list(leads_collection.find({"assigned_to": member_id}))
            
            # Calculate metrics
            total_leads = len(member_leads)
            converted_leads = len([l for l in member_leads if l.get('status') == 'closed_won'])
            revenue = sum(l.get('deal_value', 0) for l in member_leads if l.get('status') == 'closed_won')
            win_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            team_performance.append({
                "id": member_id,
                "first_name": member.get("first_name", ""),
                "last_name": member.get("last_name", ""),
                "position": member.get("position", ""),
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "revenue": revenue,
                "win_rate": win_rate
            })
        
        return {
            "team_members": team_performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team performance: {str(e)}"
        )

@router.get("/member-details/{member_id}")
async def get_member_details(
    member_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get detailed performance data for a specific team member"""
    try:
        # Check permissions
        if current_user.position != 'sales_manager' and current_user.role not in ['admin', 'director']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales manager access required."
            )
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Get member info
        try:
            member = users_collection.find_one({"_id": ObjectId(member_id)})
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team member not found"
                )
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member ID"
            )
        
        # Get member's leads in date range
        member_leads = list(leads_collection.find({
            "assigned_to": member_id,
            "created_at": {
                "$gte": start_dt,
                "$lt": end_dt
            }
        }))
        
        # Calculate performance metrics
        total_leads = len(member_leads)
        converted_leads = len([l for l in member_leads if l.get('status') == 'closed_won'])
        total_revenue = sum(l.get('deal_value', 0) for l in member_leads if l.get('status') == 'closed_won')
        win_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        avg_deal_size = (total_revenue / converted_leads) if converted_leads > 0 else 0
        
        # Get active customers
        active_customers = list(customers_collection.find({"assigned_to": member_id}))
        
        # Payment performance
        total_expected = sum(l.get('deal_value', 0) for l in member_leads if l.get('status') == 'closed_won')
        amount_collected = sum(l.get('payment_tracking', {}).get('paid_amount', 0) for l in member_leads if l.get('status') == 'closed_won')
        collection_rate = (amount_collected / total_expected * 100) if total_expected > 0 else 0
        pending_amount = total_expected - amount_collected
        
        # Lead breakdown by status
        lead_breakdown = defaultdict(lambda: {"count": 0, "value": 0})
        for lead in member_leads:
            status = lead.get('status', 'unknown')
            lead_breakdown[status]["count"] += 1
            lead_breakdown[status]["value"] += lead.get('deal_value', 0)
        
        # Calculate percentages
        for status in lead_breakdown:
            lead_breakdown[status]["percentage"] = (lead_breakdown[status]["count"] / total_leads * 100) if total_leads > 0 else 0
        
        # Recent activities (last 10 activities)
        recent_activities = []
        
        # Add lead activities
        for lead in sorted(member_leads, key=lambda x: x.get('updated_at', datetime.min), reverse=True)[:10]:
            activity_type = "Lead Updated"
            if lead.get('status') == 'closed_won':
                activity_type = "Lead Converted"
            elif lead.get('status') == 'closed_lost':
                activity_type = "Lead Closed (Lost)"
            
            recent_activities.append({
                "date": lead.get('updated_at', lead.get('created_at', datetime.now())),
                "activity": activity_type,
                "lead_name": lead.get('contact_person', 'Unknown'),
                "value": lead.get('deal_value', 0)
            })
        
        # Sort activities by date
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:10]
        
        return {
            "member": {
                "id": str(member["_id"]),
                "first_name": member.get("first_name", ""),
                "last_name": member.get("last_name", ""),
                "email": member.get("email", ""),
                "phone_number": member.get("phone_number", ""),
                "position": member.get("position", "")
            },
            "performance": {
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "win_rate": win_rate,
                "total_revenue": total_revenue,
                "avg_deal_size": avg_deal_size,
                "active_customers": len(active_customers)
            },
            "payment_performance": {
                "total_expected": total_expected,
                "amount_collected": amount_collected,
                "collection_rate": collection_rate,
                "pending_amount": pending_amount
            },
            "lead_breakdown": dict(lead_breakdown),
            "recent_activities": [serialize_object_id(activity) for activity in recent_activities],
            "customers": [serialize_object_id(customer) for customer in active_customers[:20]]  # Limit to 20 customers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member details: {str(e)}"
        )

@router.get("/reports")
async def get_sales_reports(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    team_member: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get comprehensive sales reports with performance metrics"""
    try:
        if current_user.department != 'sales':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales department only."
            )
        
        # Calculate IST timezone offset (+5:30)
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = get_ist_now() + ist_offset
        
        # Set default date range (last 30 days)
        if not start_date or not end_date:
            end_date_obj = now_ist.date()
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Convert to datetime for MongoDB queries
        start_datetime = datetime.combine(start_date_obj, datetime.min.time())
        end_datetime = datetime.combine(end_date_obj, datetime.max.time())
        
        # Build base filter
        base_filter = {
            "created_at": {
                "$gte": start_datetime,
                "$lte": end_datetime
            }
        }
        
        # Add team member filter if specified (only for sales managers)
        if team_member and current_user.position == 'sales_manager':
            base_filter["assigned_to"] = ObjectId(team_member)
        elif current_user.position != 'sales_manager':
            # Sales executives can only see their own data
            base_filter["assigned_to"] = ObjectId(current_user.id)
        
        # Get leads data
        leads_cursor = leads_collection.find(base_filter)
        leads = list(leads_cursor)
        
        # Calculate overview metrics
        total_leads = len(leads)
        converted_leads = len([l for l in leads if l.get('status') == 'closed_won'])
        win_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate revenue
        total_revenue = sum(
            lead.get('estimated_value', 0) 
            for lead in leads 
            if lead.get('status') == 'closed_won'
        )
        
        avg_deal_size = total_revenue / converted_leads if converted_leads > 0 else 0
        
        # Calculate payment metrics
        payment_collected = 0
        for lead in leads:
            if lead.get('status') == 'closed_won' and lead.get('payment_tracking'):
                payments = lead.get('payment_tracking', {}).get('payments', [])
                payment_collected += sum(p.get('amount', 0) for p in payments)
        
        # Performance trend (monthly data)
        performance_trend = []
        current_month = start_datetime.replace(day=1)
        while current_month <= end_datetime:
            month_end = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            month_leads = [
                l for l in leads 
                if current_month <= l.get('created_at', datetime.min) <= month_end
            ]
            
            month_conversions = len([
                l for l in month_leads 
                if l.get('status') == 'closed_won'
            ])
            
            performance_trend.append({
                "month": current_month.strftime("%b %Y"),
                "leads": len(month_leads),
                "conversions": month_conversions
            })
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Lead status distribution
        status_counts = defaultdict(int)
        for lead in leads:
            status_counts[lead.get('status', 'unknown')] += 1
        
        # Payment trend (monthly)
        payment_trend = []
        for trend_item in performance_trend:
            month_start = datetime.strptime(trend_item['month'], "%b %Y")
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            month_leads = [
                l for l in leads 
                if month_start <= l.get('created_at', datetime.min) <= month_end
            ]
            
            expected = sum(l.get('estimated_value', 0) for l in month_leads if l.get('status') == 'closed_won')
            collected = 0
            
            for lead in month_leads:
                if lead.get('status') == 'closed_won' and lead.get('payment_tracking'):
                    payments = lead.get('payment_tracking', {}).get('payments', [])
                    collected += sum(p.get('amount', 0) for p in payments)
            
            payment_trend.append({
                "month": trend_item['month'],
                "expected": expected,
                "collected": collected
            })
        
        # Win rate by source
        source_stats = defaultdict(lambda: {'total': 0, 'won': 0})
        for lead in leads:
            source = lead.get('source', 'unknown')
            source_stats[source]['total'] += 1
            if lead.get('status') == 'closed_won':
                source_stats[source]['won'] += 1
        
        win_rate_by_source = {
            source: (stats['won'] / stats['total'] * 100) if stats['total'] > 0 else 0
            for source, stats in source_stats.items()
        }
        
        # Calculate changes (placeholder - would need historical data for real comparison)
        leads_change = 15.2  # Mock data
        conversion_change = 8.7
        revenue_change = 12.3
        win_rate_change = 5.1
        deal_size_change = -2.1
        payment_change = 18.9
        
        return {
            "overview": {
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "win_rate": win_rate,
                "total_revenue": total_revenue,
                "avg_deal_size": avg_deal_size,
                "payment_collected": payment_collected,
                "leads_change": leads_change,
                "conversion_change": conversion_change,
                "revenue_change": revenue_change,
                "win_rate_change": win_rate_change,
                "deal_size_change": deal_size_change,
                "payment_change": payment_change
            },
            "performance_trend": performance_trend,
            "lead_status_distribution": dict(status_counts),
            "payment_trend": payment_trend,
            "win_rate_by_source": win_rate_by_source,
            "date_range": {
                "start": start_date_obj.isoformat(),
                "end": end_date_obj.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating sales reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales reports: {str(e)}"
        )

@router.get("/team-performance")
async def get_team_performance(current_user: UserInDB = Depends(get_current_user)):
    """Get team performance data for sales managers"""
    try:
        if current_user.department != 'sales' or current_user.position != 'sales_manager':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales managers only."
            )
        
        # Get all sales team members
        team_members = list(users_collection.find({
            "department": "sales",
            "position": {"$in": ["sales_executive", "sales_manager"]}
        }))
        
        team_performance = []
        
        for member in team_members:
            member_id = member["_id"]
            
            # Get member's leads
            member_leads = list(leads_collection.find({"assigned_to": member_id}))
            
            # Calculate metrics
            total_leads = len(member_leads)
            converted_leads = len([l for l in member_leads if l.get('status') == 'closed_won'])
            win_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            revenue = sum(
                lead.get('estimated_value', 0) 
                for lead in member_leads 
                if lead.get('status') == 'closed_won'
            )
            
            # Get active customers
            active_customers = customers_collection.count_documents({
                "assigned_to": member_id,
                "status": "active"
            })
            
            team_performance.append({
                "id": str(member_id),
                "first_name": member.get("first_name", ""),
                "last_name": member.get("last_name", ""),
                "email": member.get("email", ""),
                "position": member.get("position", ""),
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "win_rate": win_rate,
                "revenue": revenue,
                "active_customers": active_customers
            })
        
        return {
            "team_members": team_performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team performance: {str(e)}"
        )

@router.get("/reports")
async def get_sales_reports(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get comprehensive sales reports"""
    try:
        if current_user.role not in ['admin', 'director', 'sales_manager']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sales managers and above can access reports"
            )
        
        # Set default date range if not provided
        if not start_date:
            start_date = (get_ist_now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = get_ist_now().strftime("%Y-%m-%d")
        
        # Get leads in date range
        leads_cursor = leads_collection.find({
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        leads = list(leads_cursor)
        
        # Get customers in date range  
        customers_cursor = customers_collection.find({
            "acquisition_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
        customers = list(customers_cursor)
        
        # Calculate metrics
        total_leads = len(leads)
        converted_leads = len([l for l in leads if l.get("status") == "closed_won"])
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        total_revenue = sum([c.get("lifetime_value", 0) for c in customers])
        avg_deal_size = total_revenue / len(customers) if customers else 0
        
        # Get team performance
        team_stats = {}
        for lead in leads:
            assigned_to = lead.get("assigned_to", "unassigned")
            if assigned_to not in team_stats:
                team_stats[assigned_to] = {
                    "leads": 0,
                    "conversions": 0,
                    "revenue": 0
                }
            team_stats[assigned_to]["leads"] += 1
            if lead.get("status") == "closed_won":
                team_stats[assigned_to]["conversions"] += 1
                team_stats[assigned_to]["revenue"] += lead.get("deal_value", 0)
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "overview": {
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "conversion_rate": round(conversion_rate, 2),
                "total_revenue": total_revenue,
                "avg_deal_size": round(avg_deal_size, 2),
                "new_customers": len(customers)
            },
            "team_performance": [
                {
                    "member": member,
                    "leads": stats["leads"],
                    "conversions": stats["conversions"],
                    "conversion_rate": round(stats["conversions"] / stats["leads"] * 100, 2) if stats["leads"] > 0 else 0,
                    "revenue": stats["revenue"]
                }
                for member, stats in team_stats.items()
            ],
            "leads_by_status": {
                status: len([l for l in leads if l.get("status") == status])
                for status in ["new", "contacted", "qualified", "proposal", "closed_won", "closed_lost"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating sales reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reports: {str(e)}"
        )

@router.get("/member-details/{member_id}")
async def get_member_details(
    member_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get detailed performance metrics for a specific team member"""
    try:
        if current_user.role not in ['admin', 'director', 'sales_manager']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sales managers and above can access member details"
            )
        
        # Set default date range if not provided
        if not start_date:
            start_date = (get_ist_now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = get_ist_now().strftime("%Y-%m-%d")
        
        # Get member info
        user = users_collection.find_one({"username": member_id})
        if not user:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Get member's leads
        member_leads = list(leads_collection.find({
            "assigned_to": member_id,
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }))
        
        # Calculate performance metrics
        total_leads = len(member_leads)
        converted_leads = len([l for l in member_leads if l.get("status") == "closed_won"])
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        total_revenue = sum([l.get("deal_value", 0) for l in member_leads if l.get("status") == "closed_won"])
        
        # Get leads by status
        leads_by_status = {}
        for status in ["new", "contacted", "qualified", "proposal", "closed_won", "closed_lost"]:
            leads_by_status[status] = len([l for l in member_leads if l.get("status") == status])
        
        # Get recent activities
        recent_leads = sorted(member_leads, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]
        
        return {
            "member_info": {
                "id": member_id,
                "name": user.get("first_name", "") + " " + user.get("last_name", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "")
            },
            "performance": {
                "total_leads": total_leads,
                "converted_leads": converted_leads,
                "conversion_rate": round(conversion_rate, 2),
                "total_revenue": total_revenue,
                "avg_deal_size": round(total_revenue / converted_leads, 2) if converted_leads > 0 else 0
            },
            "leads_by_status": leads_by_status,
            "recent_activities": [
                {
                    "id": str(lead.get("_id")),
                    "company_name": lead.get("company_name"),
                    "status": lead.get("status"),
                    "deal_value": lead.get("deal_value", 0),
                    "updated_at": lead.get("updated_at")
                }
                for lead in recent_leads
            ],
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member details: {str(e)}"
        )

@router.get("/team-members")
async def get_team_members(current_user: UserInDB = Depends(get_current_user)):
    """Get sales team members (managers only)"""
    try:
        # Check permissions - Only managers can see team members
        if not is_sales_manager(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Manager access required."
            )
        
        # Get all sales team members
        sales_users = list(users_collection.find({
            "$or": [
                {"department": {"$regex": "sales", "$options": "i"}},
                {"position": {"$regex": "sales", "$options": "i"}}
            ]
        }))
        
        team_members = []
        for user in sales_users:
            team_members.append({
                "id": str(user.get("_id")),
                "username": user.get("username"),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user.get("email", ""),
                "department": user.get("department", ""),
                "position": user.get("position", ""),
                "role": user.get("role", "")
            })
        
        return team_members
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team members: {str(e)}"
        )

@router.get("/top-performers")
async def get_top_performers(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    limit: int = Query(5, description="Number of top performers to return"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get top performing sales team members"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Build query filters
        date_filter = {
            "created_at": {
                "$gte": start_dt,
                "$lt": end_dt
            }
        }
        
        # Role-based access control
        if not is_sales_manager(current_user):
            # Non-managers can only see their own performance
            return [{
                "id": str(current_user.id),
                "name": f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "department": current_user.department,
                "total_revenue": 0,
                "deals_closed": 0,
                "conversion_rate": 0.0
            }]
        
        # Get all leads in the period
        leads_cursor = leads_collection.find(date_filter)
        leads_data = list(leads_cursor)
        
        # Group by assigned_to
        performer_stats = defaultdict(lambda: {
            "total_revenue": 0,
            "deals_closed": 0,
            "total_leads": 0,
            "conversion_rate": 0.0
        })
        
        for lead in leads_data:
            assigned_to = lead.get("assigned_to")
            if not assigned_to:
                continue
                
            performer_stats[assigned_to]["total_leads"] += 1
            
            if lead.get("status") == "closed_won":
                performer_stats[assigned_to]["deals_closed"] += 1
                performer_stats[assigned_to]["total_revenue"] += lead.get("deal_value", 0)
        
        # Calculate conversion rates
        for performer_id, stats in performer_stats.items():
            if stats["total_leads"] > 0:
                stats["conversion_rate"] = (stats["deals_closed"] / stats["total_leads"]) * 100
        
        # Get user details and build performer list
        performers = []
        for performer_id, stats in performer_stats.items():
            try:
                user = users_collection.find_one({"_id": ObjectId(performer_id)})
                if not user:
                    # Try finding by username
                    user = users_collection.find_one({"username": performer_id})
                
                if user:
                    performers.append({
                        "id": str(user.get("_id")),
                        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown'),
                        "first_name": user.get("first_name", ""),
                        "last_name": user.get("last_name", ""),
                        "department": user.get("department", "Sales"),
                        "total_revenue": stats["total_revenue"],
                        "deals_closed": stats["deals_closed"],
                        "conversion_rate": round(stats["conversion_rate"], 1)
                    })
            except Exception as e:
                logger.error(f"Error processing performer {performer_id}: {str(e)}")
                continue
        
        # Sort by total revenue and limit results
        performers.sort(key=lambda x: x["total_revenue"], reverse=True)
        return performers[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top performers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top performers: {str(e)}"
        )

@router.get("/attendance/late")
async def get_late_members(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get team members who are late today (managers only)"""
    try:
        # Check permissions - Only managers can see late members
        if not is_sales_manager(current_user):
            # Non-managers get empty result
            return []
        
        # Parse date
        try:
            check_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # For demo purposes, we'll create mock late member data
        # In a real system, this would query the attendance database
        
        # Get sales team members
        sales_users = list(users_collection.find({
            "$or": [
                {"department": {"$regex": "sales", "$options": "i"}},
                {"position": {"$regex": "sales", "$options": "i"}}
            ]
        }))
        
        # Mock late members data (replace with actual attendance queries)
        late_members = []
        
        # For demonstration, mark some users as late randomly
        import random
        
        for user in sales_users[:3]:  # Only show first 3 as late for demo
            if random.choice([True, False]):  # 50% chance of being late
                late_minutes = random.randint(5, 45)
                expected_time = "09:00"
                actual_time_obj = datetime.strptime("09:00", "%H:%M") + timedelta(minutes=late_minutes)
                actual_time = actual_time_obj.strftime("%H:%M")
                
                late_members.append({
                    "id": str(user.get("_id")),
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown'),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "department": user.get("department", "Sales"),
                    "expected_time": expected_time,
                    "check_in_time": actual_time,
                    "late_minutes": late_minutes
                })
        
        return late_members
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting late members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get late members: {str(e)}"
        )

from fastapi import Body

@router.post("/attendance/check-in")
async def check_in(
    attendance_data: Optional[Dict[str, Any]] = Body(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """Check in for the current user"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )

        # Get current IST time
        now_ist = get_ist_now()
        today_str = now_ist.strftime("%Y-%m-%d")
        time_str = now_ist.strftime("%H:%M:%S")

        # Office timings (IST)
        office_start = now_ist.replace(hour=10, minute=0, second=0, microsecond=0)  # 10:00 AM
        late_threshold = now_ist.replace(hour=10, minute=15, second=0, microsecond=0)  # 10:15 AM

        # Determine status
        if now_ist <= office_start:
            status = "early"
        elif now_ist <= late_threshold:
            status = "on_time"
        else:
            status = "late"

        # Calculate late minutes if applicable
        late_minutes = 0
        if status == "late":
            late_minutes = int((now_ist - late_threshold).total_seconds() / 60)

        # Extract optional fields from request body
        check_in_location = None
        check_in_note = None
        if attendance_data:
            check_in_location = attendance_data.get("check_in_location")
            check_in_note = attendance_data.get("check_in_note")

        # Create attendance record (in a real system, this would go to attendance collection)
        attendance_record = {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "date": today_str,
            "check_in_time": time_str,
            "status": status,
            "late_minutes": late_minutes,
            "created_at": now_ist,
            "check_in_location": check_in_location,
            "check_in_note": check_in_note
        }

        # Here you would save to attendance collection
        # attendance_collection.insert_one(attendance_record)

        return {
            "message": f"Checked in successfully at {time_str}",
            "status": status,
            "check_in_time": time_str,
            "late_minutes": late_minutes,
            "office_start": "10:00",
            "late_threshold": "10:15",
            "check_in_location": check_in_location,
            "check_in_note": check_in_note
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during check-in: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check in: {str(e)}"
        )

@router.post("/attendance/check-out")
async def check_out(
    current_user: UserInDB = Depends(get_current_user)
):
    """Check out for the current user"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Get current IST time
        now_ist = get_ist_now()
        today_str = now_ist.strftime("%Y-%m-%d")
        time_str = now_ist.strftime("%H:%M:%S")
        
        # Office end time (IST)
        office_end = now_ist.replace(hour=18, minute=0, second=0, microsecond=0)  # 6:00 PM
        
        # Determine status
        if now_ist >= office_end:
            status = "on_time"
        else:
            status = "early"
            
        # Here you would update attendance record
        # attendance_collection.update_one(
        #     {"user_id": str(current_user.id), "date": today_str},
        #     {"$set": {"check_out_time": time_str, "check_out_status": status}}
        # )
        
        return {
            "message": f"Checked out successfully at {time_str}",
            "status": status,
            "check_out_time": time_str,
            "office_end": "18:00"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during check-out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check out: {str(e)}"
        )

@router.get("/attendance/my-status")
async def get_my_attendance_status(
    date: str = Query(None, description="Date in YYYY-MM-DD format (defaults to today)"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get current user's attendance status"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Get date (default to today)
        if not date:
            date = get_ist_now().strftime("%Y-%m-%d")
        
        # Mock attendance data (replace with actual attendance collection query)
        # In real implementation:
        # attendance = attendance_collection.find_one({
        #     "user_id": str(current_user.id),
        #     "date": date
        # })
        
        # Mock data for demo
        now_ist = get_ist_now()
        if now_ist.hour >= 10:  # After 10 AM, show as checked in
            return {
                "date": date,
                "is_checked_in": True,
                "check_in_time": "09:45:00",
                "status": "on_time",
                "late_minutes": 0,
                "is_checked_out": now_ist.hour >= 18,
                "check_out_time": "18:30:00" if now_ist.hour >= 18 else None
            }
        else:
            return {
                "date": date,
                "is_checked_in": False,
                "check_in_time": None,
                "status": "not_checked_in",
                "late_minutes": 0,
                "is_checked_out": False,
                "check_out_time": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance status: {str(e)}"
        )

@router.get("/attendance/status")
async def get_attendance_status(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get attendance status summary for sales team"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Get sales team members
        sales_users = list(users_collection.find({
            "$or": [
                {"department": {"$regex": "sales", "$options": "i"}},
                {"position": {"$regex": "sales", "$options": "i"}}
            ]
        }))
        
        total_executives = len(sales_users)
        present_count = 0
        late_count = 0
        absent_count = 0
        
        # Mock attendance calculation (replace with actual attendance system)
        import random
        for user in sales_users:
            # Simulate attendance status
            status = random.choice(['present', 'late', 'absent'])
            if status == 'present':
                present_count += 1
            elif status == 'late':
                late_count += 1
            else:
                absent_count += 1
        
        return {
            "summary": {
                "total": total_executives,
                "present": present_count,
                "late": late_count,
                "absent": absent_count
            },
            "date": date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance status: {str(e)}"
        )

@router.get("/executive-reports")
async def get_executive_reports(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get executive-wise reports with role-based access"""
    try:
        # Check permissions
        if not is_sales_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Sales access required."
            )
        
        # Parse date and convert to IST
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Convert to IST timezone (UTC+5:30)
            ist_offset = timedelta(hours=5, minutes=30)
            ist_date = report_date.replace(tzinfo=timezone.utc) + ist_offset
            
            # Set start and end of day in IST
            start_of_day = ist_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = ist_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        executives = []
        
        # Role-based access control
        if is_sales_manager(current_user):
            # Managers can see all executives
            logger.info(f"Manager {current_user.username} accessing all executive reports")
            sales_users = list(users_collection.find({
                "$or": [
                    {"department": "Sales"},
                    {"department": "sales"},
                    {"position": {"$regex": "sales", "$options": "i"}}
                ]
            }))
            logger.info(f"Found {len(sales_users)} sales users for manager view")
        else:
            # Employees can only see their own data
            logger.info(f"Employee {current_user.username} accessing own reports")
            user_data = users_collection.find_one({"_id": current_user.id})
            sales_users = [user_data] if user_data else []
        
        for user in sales_users:
            if not user:
                continue
                
            user_id = str(user.get("_id"))
            username = user.get("username", "")
            
            # Get today's leads for this executive (both by user_id and username)
            leads_today = list(leads_collection.find({
                "$or": [
                    {"assigned_to": user_id},
                    {"assigned_to": username}
                ],
                "created_at": {
                    "$gte": start_of_day.replace(tzinfo=None),
                    "$lte": end_of_day.replace(tzinfo=None)
                }
            }))
            
            # Calculate metrics
            leads_worked_today = len(leads_today)
            leads_won = len([l for l in leads_today if l.get('status') == 'closed_won'])
            amount_collected = 0
            
            # Calculate amount collected from payment tracking
            for lead in leads_today:
                if lead.get('status') == 'closed_won':
                    if lead.get('payment_tracking'):
                        amount_collected += lead['payment_tracking'].get('paid_amount', 0)
                    else:
                        # If no payment tracking, consider deal value as collected
                        amount_collected += lead.get('deal_value', 0)
            
            conversion_rate = (leads_won / leads_worked_today * 100) if leads_worked_today > 0 else 0
            
            # Generate realistic attendance status based on current IST time
            current_ist = get_ist_now()
            office_start = current_ist.replace(hour=10, minute=0, second=0, microsecond=0)  # 10:00 AM IST
            late_threshold = current_ist.replace(hour=10, minute=15, second=0, microsecond=0)  # 10:15 AM IST
            
            # Mock attendance status (replace with actual attendance system)
            import random
            if current_ist.hour < 10:
                attendance_status = "not_checked_in"
                check_in_time = None
            else:
                # Simulate realistic attendance
                attendance_choice = random.choices(
                    ['present', 'late', 'absent'], 
                    weights=[70, 20, 10]  # 70% present, 20% late, 10% absent
                )[0]
                
                if attendance_choice == 'present':
                    # Present: checked in between 9:30-10:00
                    check_in_minutes = random.randint(30, 60)  # 30-60 minutes past 9
                    check_in_time = f"09:{check_in_minutes:02d}"
                    attendance_status = "present"
                elif attendance_choice == 'late':
                    # Late: checked in after 10:15
                    late_minutes = random.randint(16, 60)  # 16-60 minutes past 10
                    check_in_time = f"10:{late_minutes:02d}"
                    attendance_status = "late"
                else:
                    # Absent
                    check_in_time = None
                    attendance_status = "absent"
            
            executives.append({
                "id": user_id,
                "username": username,
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or username,
                "position": user.get("position", "Sales Executive"),
                "department": user.get("department", "Sales"),
                "attendance_status": attendance_status,
                "check_in_time": check_in_time,
                "leads_worked_today": leads_worked_today,
                "leads_won": leads_won,
                "amount_collected": amount_collected,
                "conversion_rate": round(conversion_rate, 1)
            })
        
        return {
            "executives": executives,
            "date": date,
            "access_level": "manager" if is_sales_manager(current_user) else "employee",
            "current_ist_time": get_ist_now().strftime("%H:%M"),
            "office_timing": {
                "start": "10:00",
                "late_threshold": "10:15"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executive reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executive reports: {str(e)}"
        )

@router.get("/attendance/issues")
async def get_attendance_issues(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get attendance issues (late/absent members) for the specified date"""
    try:
        # Check permissions - Only managers can see attendance issues
        if not is_sales_manager(current_user):
            return {"issues": []}
        
        # Parse date
        try:
            check_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Get sales team members
        sales_users = list(users_collection.find({
            "$or": [
                {"department": {"$regex": "sales", "$options": "i"}},
                {"position": {"$regex": "sales", "$options": "i"}}
            ]
        }))
        
        issues = []
        
        # Mock attendance issues (replace with actual attendance system)
        import random
        
        for user in sales_users[:3]:  # Show first 3 users with potential issues
            issue_type = random.choice(['late', 'absent', None])
            
            if issue_type == 'late':
                # Late after 10:15 AM
                late_minutes = random.randint(5, 60)
                check_in_hour = 10
                check_in_minute = 15 + late_minutes
                if check_in_minute >= 60:
                    check_in_hour += 1
                    check_in_minute -= 60
                
                check_in_time = f"{check_in_hour:02d}:{check_in_minute:02d}"
                
                issues.append({
                    "id": str(user.get("_id")),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown'),
                    "status": "late",
                    "check_in_time": check_in_time,
                    "late_minutes": late_minutes,
                    "expected_time": "10:00"
                })
            elif issue_type == 'absent':
                issues.append({
                    "id": str(user.get("_id")),
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'Unknown'),
                    "status": "absent",
                    "check_in_time": None,
                    "late_minutes": 0,
                    "expected_time": "10:00"
                })
        
        return {
            "issues": issues,
            "date": date,
            "office_hours": {
                "start_time": "10:00",
                "late_threshold": "10:15"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance issues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance issues: {str(e)}"
        )

def is_sales_manager(user: UserInDB) -> bool:
    """Check if user is a sales manager"""
    # Check role first
    if user.role and user.role.lower() in ['admin', 'director', 'manager']:
        return True
    
    # Check position
    position = user.position.lower() if user.position else ""
    if 'sales_manager' in position or 'manager' in position:
        return True
    
    # Check if user is in sales department and has manager role
    if user.department and user.department.lower() == 'sales' and user.role and user.role.lower() == 'manager':
        return True
    
    return False

def is_sales_user(user: UserInDB) -> bool:
    """Check if user belongs to sales department"""
    # Check if user is in sales department
    if user.department and user.department.lower() == 'sales':
        return True
    
    # Check if user has sales position
    if user.position and user.position.lower() in ['sales_manager', 'sales_executive']:
        return True
    
    # Check if user has admin/director role (they can access all departments)
    if user.role and user.role.lower() in ['admin', 'director']:
        return True
    
    return False
