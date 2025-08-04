from datetime import datetime
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel, Field
from app.database import db

# Create the salary_slips collection
salary_slips_collection = db["salary_slips"]

# Pydantic models
class SalarySlip(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    employee_id: str
    employee_name: Optional[str] = None
    department: Optional[str] = None
    month: str
    year: int
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    gross_salary: float
    net_salary: float
    status: str = "pending"  # pending, paid, cancelled
    pay_date: Optional[datetime] = None
    paid_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class SalarySlipResponse(BaseModel):
    id: str = Field(alias="_id")
    employee_id: str
    employee_name: Optional[str] = None
    department: Optional[str] = None
    month: str
    year: int
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    gross_salary: float
    net_salary: float
    status: str = "pending"  # pending, paid, cancelled
    pay_date: Optional[datetime] = None
    paid_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

# Ensure indexes
try:
    salary_slips_collection.create_index([("employee_id", 1), ("month", 1), ("year", 1)], unique=True)
    salary_slips_collection.create_index([("department", 1)])
    salary_slips_collection.create_index([("status", 1)])
except Exception as e:
    print(f"Warning: Error creating indexes on salary_slips: {e}")

# Methods for interacting with salary slips
class DatabaseSalarySlips:
    @staticmethod
    async def get_salary_slip(employee_id, month, year):
        """Get a specific salary slip"""
        result = salary_slips_collection.find_one({
            "employee_id": employee_id,
            "month": month,
            "year": int(year)
        })
        return result

    @staticmethod
    async def get_salary_slips_by_period(month, year, department=None):
        """Get all salary slips for a specific period"""
        query = {
            "month": month,
            "year": int(year)
        }
        
        if department:
            query["department"] = department
            
        results = list(salary_slips_collection.find(query))
        return results

    @staticmethod
    async def mark_salary_slip_as_paid(employee_id, month, year, user_id):
        """Mark a salary slip as paid"""
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
                    "paid_by": user_id
                }
            }
        )
        return result.matched_count > 0

    @staticmethod
    async def get_user_salary_slips(employee_id: str):
        """Get all salary slips for a specific employee"""
        try:
            results = list(salary_slips_collection.find({"employee_id": employee_id}).sort("year", -1).sort("month", -1))
            return [SalarySlip(**slip) for slip in results]
        except Exception as e:
            print(f"Error fetching user salary slips: {e}")
            return []

    @staticmethod
    async def get_salary_slip_by_id(slip_id: str):
        """Get a salary slip by its ID"""
        try:
            result = salary_slips_collection.find_one({"_id": ObjectId(slip_id)})
            if result:
                return SalarySlip(**result)
            return None
        except Exception as e:
            print(f"Error fetching salary slip by ID: {e}")
            return None

    @staticmethod
    async def create_salary_slip(slip_data: dict):
        """Create a new salary slip"""
        try:
            slip_data["created_at"] = datetime.utcnow()
            slip_data["updated_at"] = datetime.utcnow()
            result = salary_slips_collection.insert_one(slip_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating salary slip: {e}")
            return None

    @staticmethod
    async def update_salary_slip(slip_id: str, update_data: dict):
        """Update a salary slip"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = salary_slips_collection.update_one(
                {"_id": ObjectId(slip_id)},
                {"$set": update_data}
            )
            return result.matched_count > 0
        except Exception as e:
            print(f"Error updating salary slip: {e}")
            return False
