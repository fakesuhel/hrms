from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema

# Get salary_slips collection
salary_slips_collection = db["salary_slips"]


# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now()

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, v, info=None):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Dict[str, Any], handler) -> Dict[str, Any]:
        return {"type": "string"}

class SalarySlipBase(BaseModel):
    user_id: str
    employee_id: str
    month: int  # 1-12
    year: int
    
    # Employee Information
    employee_name: str
    department: str
    designation: str
    join_date: str
    
    # Salary Components
    base_salary: float
    hra: float = 0.0
    allowances: float = 0.0
    performance_incentives: float = 0.0
    gross_salary: float
    
    # Deductions
    pf_deduction: float = 0.0
    tax_deduction: float = 0.0
    penalty_deductions: float = 0.0
    other_deductions: float = 0.0
    total_deductions: float
    
    # Final Amount
    net_salary: float
    
    # Work Details
    working_days: int = 22
    present_days: int
    absent_days: int = 0
    paid_leaves: int = 0
    
    # Status
    status: str = "generated"  # "generated", "approved", "paid"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class SalarySlipCreate(SalarySlipBase):
    pass

class SalarySlipUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class SalarySlipInDB(SalarySlipBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=get_ist_now)
    updated_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class SalarySlipResponse(SalarySlipBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class DatabaseSalarySlips:
    @staticmethod
    async def create_salary_slip(slip_data: SalarySlipCreate) -> SalarySlipInDB:
        # Check if slip already exists for this user, month, year
        existing_slip = salary_slips_collection.find_one({
            "user_id": slip_data.user_id,
            "month": slip_data.month,
            "year": slip_data.year
        })
        
        if existing_slip:
            raise ValueError(f"Salary slip already exists for {slip_data.month}/{slip_data.year}")
        
        slip_dict = slip_data.model_dump()
        slip_dict["created_at"] = get_ist_now()
        slip_dict["updated_at"] = get_ist_now()
        
        result = salary_slips_collection.insert_one(slip_dict)
        slip_dict["_id"] = result.inserted_id
        
        return SalarySlipInDB(**slip_dict)
    
    @staticmethod
    async def get_user_salary_slips(user_id: str, limit: int = 12) -> List[SalarySlipInDB]:
        slips = list(salary_slips_collection.find(
            {"user_id": user_id}
        ).sort([("year", -1), ("month", -1)]).limit(limit))
        
        return [SalarySlipInDB(**slip) for slip in slips]
    
    @staticmethod
    async def get_salary_slip_by_id(slip_id: str) -> Optional[SalarySlipInDB]:
        try:
            id_obj = ObjectId(slip_id) if isinstance(slip_id, str) else slip_id
            slip = salary_slips_collection.find_one({"_id": id_obj})
            if slip:
                return SalarySlipInDB(**slip)
            return None
        except Exception as e:
            print(f"Error in get_salary_slip_by_id: {e}")
            return None
    
    @staticmethod
    async def get_salary_slip_by_month_year(user_id: str, month: int, year: int) -> Optional[SalarySlipInDB]:
        slip = salary_slips_collection.find_one({
            "user_id": user_id,
            "month": month,
            "year": year
        })
        if slip:
            return SalarySlipInDB(**slip)
        return None
    
    @staticmethod
    async def update_salary_slip(slip_id: str, update_data: SalarySlipUpdate) -> Optional[SalarySlipInDB]:
        try:
            id_obj = ObjectId(slip_id) if isinstance(slip_id, str) else slip_id
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_ist_now()
            
            result = salary_slips_collection.update_one(
                {"_id": id_obj},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_slip = salary_slips_collection.find_one({"_id": id_obj})
                return SalarySlipInDB(**updated_slip)
            return None
        except Exception as e:
            print(f"Error in update_salary_slip: {e}")
            return None
    
    @staticmethod
    async def delete_salary_slip(slip_id: str) -> bool:
        try:
            id_obj = ObjectId(slip_id) if isinstance(slip_id, str) else slip_id
            result = salary_slips_collection.delete_one({"_id": id_obj})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error in delete_salary_slip: {e}")
            return False
