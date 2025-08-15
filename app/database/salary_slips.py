from datetime import datetime
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel, Field
from app.database import db
from zoneinfo import ZoneInfo

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)

# Create the salary_slips collection
salary_slips_collection = db["salary_slips"]

# Ensure indexes
try:
    salary_slips_collection.create_index([("employee_id", 1), ("month", 1), ("year", 1)], unique=True)
    salary_slips_collection.create_index([("department", 1)])
    salary_slips_collection.create_index([("status", 1)])
except Exception as e:
    print(f"Warning: Error creating indexes on salary_slips: {e}")

class SalarySlipResponse(BaseModel):
    id: Optional[str] = Field(alias="_id")
    employee_id: str
    month: str
    year: int
    department: Optional[str] = None
    status: Optional[str] = None
    pay_date: Optional[datetime] = None
    paid_by: Optional[str] = None
    base_salary: Optional[float] = None
    net_salary: Optional[float] = None
    allowances: Optional[float] = None
    hra: Optional[float] = None
    pf_deduction: Optional[float] = None
    tax_deduction: Optional[float] = None
    penalty_deductions: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat() if v else None
        }

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
                    "pay_date": get_kolkata_now(),
                    "paid_by": user_id
                }
            }
        )
        return result.matched_count > 0
