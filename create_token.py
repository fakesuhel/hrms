#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/home/ubuntu/test/company_crm')

from app.utils.auth import create_access_token

async def main():
    # Create token for the first user
    user_id = "687c18d8b9d651784b15c331"
    token = create_access_token(data={"sub": user_id})
    print(f"User ID: {user_id}")
    print(f"Token: {token}")

if __name__ == "__main__":
    asyncio.run(main())
