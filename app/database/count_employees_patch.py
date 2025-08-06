from app.database import users_collection

class DatabaseUsers:
    @staticmethod
    async def count_employees() -> int:
        """Return the total number of active employees (not admin)"""
        return users_collection.count_documents({"is_active": True, "role": {"$ne": "admin"}})
