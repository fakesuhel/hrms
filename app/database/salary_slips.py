from datetime import datetime
from bson import ObjectId
from app.database import db

# Create the salary_slips collection
salary_slips_collection = db["salary_slips"]

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
