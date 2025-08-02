#!/usr/bin/env python3
"""Create sample attendance data for testing"""

import sys
import os
sys.path.append('/home/ubuntu/test/company_crm')

from app.database.attendance import attendance_collection
from app.database.users import users_collection
from datetime import datetime, date, timedelta
from bson import ObjectId

def create_sample_attendance():
    print("Creating sample attendance data...")
    
    # Get all active users
    users = list(users_collection.find({"is_active": True}))
    print(f"Found {len(users)} active users")
    
    if not users:
        print("No active users found!")
        return
    
    # Clear existing attendance data for current month
    current_month = date.today().replace(day=1)
    attendance_collection.delete_many({
        "date": {"$gte": current_month.isoformat()}
    })
    print("Cleared existing attendance data for current month")
    
    # Create attendance records for last 30 days
    today = date.today()
    sample_records = []
    
    for user in users[:5]:  # Only first 5 users for testing
        user_id = str(user["_id"])
        user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        
        for days_ago in range(30):  # Last 30 days
            attendance_date = today - timedelta(days=days_ago)
            
            # Skip weekends
            if attendance_date.weekday() >= 5:
                continue
            
            # 90% chance of attendance
            import random
            if random.random() < 0.9:
                check_in_time = f"09:{random.randint(0, 30):02d}:00"
                check_out_time = f"18:{random.randint(0, 30):02d}:00"
                is_late = check_in_time > "09:15:00"
                
                record = {
                    "user_id": user_id,
                    "date": attendance_date.isoformat(),
                    "check_in": check_in_time,
                    "check_out": check_out_time,
                    "check_in_location": "Office",
                    "check_out_location": "Office",
                    "work_hours": 8.0 + random.uniform(-1, 1),
                    "is_late": is_late,
                    "status": "present",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                sample_records.append(record)
                print(f"Added attendance for {user_name} on {attendance_date}")
    
    if sample_records:
        result = attendance_collection.insert_many(sample_records)
        print(f"Created {len(result.inserted_ids)} attendance records")
    else:
        print("No sample records created")

if __name__ == "__main__":
    create_sample_attendance()
