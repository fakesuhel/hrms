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

def _convert_objectid_to_str(doc):
    """Convert ObjectId to string in a document"""
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

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
    employee_name: Optional[str] = None
    employee_number: Optional[str] = None
    month: str
    year: int
    department: Optional[str] = None
    designation: Optional[str] = None
    join_date: Optional[str] = None
    working_days: Optional[int] = None
    present_days: Optional[int] = None
    absent_days: Optional[int] = None
    status: Optional[str] = None
    pay_date: Optional[datetime] = None
    paid_by: Optional[str] = None
    base_salary: Optional[float] = None
    hra: Optional[float] = None
    allowances: Optional[float] = None
    performance_incentives: Optional[float] = None
    pf_deduction: Optional[float] = None
    tax_deduction: Optional[float] = None
    penalty_deductions: Optional[float] = None
    other_deductions: Optional[float] = None
    net_salary: Optional[float] = None
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

    @staticmethod
    async def get_user_salary_slips(user_id):
        """Get all salary slips for a specific user"""
        results = list(salary_slips_collection.find({"employee_id": user_id}).sort("year", -1).sort("month", -1))
        return [SalarySlipResponse(**_convert_objectid_to_str(result)) for result in results]

    @staticmethod
    async def get_salary_slip_by_id(slip_id):
        """Get a salary slip by its ID"""
        try:
            result = salary_slips_collection.find_one({"_id": ObjectId(slip_id)})
            if result:
                return SalarySlipResponse(**_convert_objectid_to_str(result))
            return None
        except Exception:
            return None

    @staticmethod
    async def get_salary_slip_by_month_year(user_id, month, year):
        """Get salary slip for a specific user, month and year"""
        result = salary_slips_collection.find_one({
            "employee_id": user_id,
            "month": str(month),
            "year": int(year)
        })
        if result:
            return SalarySlipResponse(**_convert_objectid_to_str(result))
        return None

    @staticmethod
    async def get_all_salary_slips_for_hr():
        """Get all salary slips for HR management"""
        results = list(salary_slips_collection.find({}).sort("year", -1).sort("month", -1))
        return [SalarySlipResponse(**_convert_objectid_to_str(result)) for result in results]

    @staticmethod
    async def get_employee_salary_slips(employee_id):
        """Get all salary slips for a specific employee (for HR access)"""
        results = list(salary_slips_collection.find({"employee_id": employee_id}).sort("year", -1).sort("month", -1))
        return [SalarySlipResponse(**_convert_objectid_to_str(result)) for result in results]

    @staticmethod
    async def create_salary_slip(slip_data):
        """Create a new salary slip"""
        slip_data["created_at"] = get_kolkata_now()
        slip_data["updated_at"] = get_kolkata_now()
        slip_data["status"] = "generated"
        
        result = salary_slips_collection.insert_one(slip_data)
        if result.inserted_id:
            return await DatabaseSalarySlips.get_salary_slip_by_id(str(result.inserted_id))
        return None
