import asyncio
import os
import sys

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_db

async def main():
    db = get_db()
    c = await db["companies"].find_one({"email": "techcorp@company.com"})
    if c:
        print(f"Company: {c.get('name')}, Email: {c.get('email')}, Balance: {c.get('csr_balance')}, Reserved: {c.get('reserved_amount')}")
    else:
        print("Company not found")

if __name__ == "__main__":
    asyncio.run(main())
