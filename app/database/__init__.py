from pymongo import MongoClient
from pymongo.database import Database
import os

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://test:test123@cluster0.g3zdcff.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "bhoomi_techzone_hrms")

# Create MongoDB client
client = MongoClient(MONGO_URI)
db: Database = client[DB_NAME]

# Collections
users_collection = db["users"]
attendance_collection = db["attendance"]
projects_collection = db["projects"]
teams_collection = db["teams"]
daily_reports_collection = db["daily_reports"]
leave_requests_collection = db["leave_requests"]
performance_reviews_collection = db["performance_reviews"]
settings_collection = db["settings"]
leads_collection = db["leads"]
customers_collection = db["customers"]

# Create indices for better query performance
users_collection.create_index("email", unique=True)
users_collection.create_index("username", unique=True)
attendance_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
projects_collection.create_index("name", unique=True)
leave_requests_collection.create_index([("user_id", 1), ("start_date", 1)])
performance_reviews_collection.create_index([("user_id", 1), ("review_period", 1)])
leads_collection.create_index([("assigned_to", 1), ("status", 1)])
leads_collection.create_index([("created_by", 1), ("created_at", 1)])
customers_collection.create_index([("assigned_to", 1), ("status", 1)])
customers_collection.create_index([("created_by", 1), ("created_at", 1)])

def get_db():
    return db