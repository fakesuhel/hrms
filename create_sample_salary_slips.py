#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.salary_slips import DatabaseSalarySlips, salary_slips_collection
from app.database.users import users_collection
from datetime import datetime, timezone, timedelta
import random

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.now(IST)

async def create_sample_salary_slips():
    """Create sample salary slips for testing"""
    
    # Get all users
    users = list(users_collection.find({"is_active": True}))
    
    if not users:
        print("No users found in database")
        return
    
    now = get_ist_now()
    current_month = now.strftime("%B")  # e.g., "August"
    current_year = now.year
    
    print(f"Creating salary slips for {current_month} {current_year}")
    
    for user in users:
        try:
            user_id = str(user["_id"])
            employee_name = user.get("full_name", user.get("username", "Unknown"))
            department = user.get("department", "General")
            
            # Generate sample salary data
            basic_salary = random.randint(30000, 80000)
            allowances = round(basic_salary * 0.15)  # 15% allowances
            deductions = round(basic_salary * 0.12)  # 12% deductions (PF, tax, etc.)
            gross_salary = basic_salary + allowances
            net_salary = gross_salary - deductions
            
            # Check if salary slip already exists
            existing = await DatabaseSalarySlips.get_salary_slip(user_id, current_month, current_year)
            if existing:
                print(f"Salary slip already exists for {employee_name}")
                continue
            
            # Create salary slip data
            slip_data = {
                "employee_id": user_id,
                "employee_name": employee_name,
                "department": department,
                "month": current_month,
                "year": current_year,
                "basic_salary": float(basic_salary),
                "allowances": float(allowances),
                "deductions": float(deductions),
                "gross_salary": float(gross_salary),
                "net_salary": float(net_salary),
                "status": "paid",
                "pay_date": now,
                "paid_by": "system",
                "created_at": now,
                "updated_at": now
            }
            
            # Insert directly to avoid async issues
            result = salary_slips_collection.insert_one(slip_data)
            print(f"✅ Created salary slip for {employee_name}: ₹{net_salary:,.2f}")
            
        except Exception as e:
            print(f"❌ Error creating salary slip for {employee_name}: {e}")
    
    print("\nSample salary slips creation completed!")

if __name__ == "__main__":
    asyncio.run(create_sample_salary_slips())
