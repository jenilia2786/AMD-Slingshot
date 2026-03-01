import asyncio
import os
import sys

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_db

async def main():
    db = get_db()
    
    print("--- COMPANIES ---")
    companies = await db["companies"].find({}).to_list(length=100)
    for c in companies:
        print(f"Email: {c.get('email')}, Name: {c.get('name')}, Balance: {c.get('csr_balance')}")
        
    print("\n--- STUDENTS ---")
    students = await db["students"].find({}).to_list(length=100)
    for s in students:
        print(f"Email: {s.get('email')}, Name: {s.get('name')}, Balance: {s.get('wallet_balance')}")

    print("\n--- TASKS ---")
    tasks = await db["tasks"].find({}).to_list(length=100)
    print(f"Total Tasks: {len(tasks)}")

if __name__ == "__main__":
    asyncio.run(main())
