from database.connection import get_db, to_oid
from datetime import datetime
from fastapi import HTTPException

db = get_db()

async def reserve_funds(company_id: str, amount: int, task_id: str):
    """Reserve Reward pools for a specific task."""
    company = await db["companies"].find_one({"_id": to_oid(company_id)})
    if not company:
        raise HTTPException(status_code=404, detail="Company wallet not found")

    if company.get("csr_balance", 0) < amount:
        raise HTTPException(status_code=400, detail="Insufficient CSR balance to post task")

    # Update company: decrease balance, increase reserved
    await db["companies"].update_one(
        {"_id": company["_id"]},
        {
            "$inc": {
                "csr_balance": -amount,
                "reserved_amount": amount
            }
        }
    )
    
    # Log transaction
    await db["transactions"].insert_one({
        "type": "RESERVE",
        "company_id": str(company["_id"]),
        "task_id": task_id,
        "amount": amount,
        "status": "locked",
        "timestamp": datetime.now().isoformat()
    })

async def release_reward(task_id: str, student_id: str, company_id: str, amount: int):
    """Effectively pay the student from the reserved Reward pools."""
    # 1. Deduct from reserved
    res = await db["companies"].update_one(
        {"_id": to_oid(company_id)},
        {"$inc": {"reserved_amount": -amount}}
    )
    
    # If not found by oid, try email or other means? No, just use _id with to_oid
    if res.modified_count == 0:
        pass # Already handled by starting with to_oid

    # 2. Credit student
    student = await db["students"].find_one({"_id": to_oid(student_id)})
    if not student:
        # Fallback to email search if needed
        student = await db["students"].find_one({"email": student_id})
    
    if student:
        await db["students"].update_one(
            {"_id": student["_id"]},
            {"$inc": {"wallet_balance": amount, "total_earned": amount}}
        )
    
    # 3. Log transaction
    await db["transactions"].insert_one({
        "type": "PAYMENT",
        "from_entity": company_id,
        "to_entity": student_id,
        "task_id": task_id,
        "amount": amount,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    })
