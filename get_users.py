#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/home/ubuntu/test/company_crm')

from app.database.users import DatabaseUsers

async def main():
    users = await DatabaseUsers.get_all_users()
    if users:
        for i, user in enumerate(users[:5]):
            print(f'User {i+1}: ID={user.id}, Name={user.first_name} {user.last_name}, Role={user.role}')
    else:
        print('No users found')

if __name__ == "__main__":
    asyncio.run(main())
