#!/usr/bin/env python3
"""
Clean up attendance data with invalid datetime formats
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

# Use same connection as the app
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://test:test123@cluster0.g3zdcff.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "bhoomi_techzone_hrms")

# Database connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
attendance_collection = db["attendance"]

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

def clean_attendance_data():
    """Clean up attendance records with invalid datetime data"""
    print("Starting attendance data cleanup...")
    
    # Find all attendance records
    all_records = list(attendance_collection.find({}))
    print(f"Found {len(all_records)} attendance records to check")
    
    cleaned_count = 0
    for record in all_records:
        record_id = record["_id"]
        updates = {}
        
        # Check check_in field
        check_in = record.get("check_in")
        if check_in and isinstance(check_in, str) and len(check_in) <= 5 and ':' in check_in:
            print(f"Fixing invalid check_in time '{check_in}' in record {record_id}")
            updates["check_in"] = None
        
        # Check check_out field
        check_out = record.get("check_out")
        if check_out and isinstance(check_out, str) and len(check_out) <= 5 and ':' in check_out:
            print(f"Fixing invalid check_out time '{check_out}' in record {record_id}")
            updates["check_out"] = None
        
        # Apply updates if needed
        if updates:
            attendance_collection.update_one(
                {"_id": record_id},
                {"$set": updates}
            )
            cleaned_count += 1
    
    print(f"Cleaned {cleaned_count} attendance records")
    print("Attendance data cleanup completed!")

if __name__ == "__main__":
    clean_attendance_data()
