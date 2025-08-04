#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.users import users_collection
from app.database.salary_slips import salary_slips_collection

async def check_user_data():
    admin_user = users_collection.find_one({'username': 'admin'})
    if admin_user:
        print(f'Admin user ID: {admin_user["_id"]}')
        print(f'Admin employee_id: {admin_user.get("employee_id", "Not set")}')
    
    slip = list(salary_slips_collection.find({}).limit(1))
    if slip:
        print(f'Sample slip employee_id: {slip[0]["employee_id"]}')
    
    print("\nAll slips:")
    for slip in salary_slips_collection.find({}):
        print(f"Employee ID: {slip['employee_id']}, Name: {slip.get('employee_name', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(check_user_data())
