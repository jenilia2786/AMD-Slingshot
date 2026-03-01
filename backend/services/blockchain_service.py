"""
Simulated Blockchain Transaction Logging
Uses SHA256 hashing to create immutable transaction records.
Each block links to the previous hash, forming a verifiable chain.
"""
from database.connection import get_db, to_oid
import hashlib
from datetime import datetime
from typing import Optional

db = get_db()

async def calculate_hash(data: dict) -> str:
    """Calculate SHA256 hash of transaction data"""
    content = (
        f"{data.get('timestamp', '')}"
        f"{data.get('from_id', '')}"
        f"{data.get('to_id', '')}"
        f"{data.get('amount', 0)}"
        f"{data.get('previous_hash', '')}"
        f"{data.get('task_id', '')}"
    )
    return hashlib.sha256(content.encode()).hexdigest()


async def add_transaction(
    tx_type: str,
    from_id: str,
    from_name: str,
    to_id: str,
    to_name: str,
    amount: int,
    task_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Add a new transaction to the blockchain ledger (MongoDB).
    """
    # Get last transaction to link the hash
    last_tx = await db["transactions"].find_one(sort=[("timestamp", -1)])
    last_hash = last_tx.get("current_hash", "0000000000000000").replace("0x", "") if last_tx else "0000000000000000"

    timestamp = datetime.utcnow().isoformat() + "Z"

    raw_data = {
        "timestamp": timestamp,
        "from_id": from_id,
        "to_id": to_id,
        "amount": amount,
        "previous_hash": last_hash,
        "task_id": task_id or "",
    }

    current_hash = await calculate_hash(raw_data)

    transaction = {
        "timestamp": timestamp,
        "type": tx_type,
        "from_entity": {"type": "company_csr", "id": from_id, "name": from_name},
        "to_entity": {"type": "student", "id": to_id, "name": to_name},
        "amount": amount,
        "task_id": task_id,
        "previous_hash": "0x" + last_hash[:16].upper(),
        "current_hash": "0x" + current_hash[:16].upper(),
        "verified": True,
        "metadata": metadata or {},
    }

    result = await db["transactions"].insert_one(transaction)
    transaction["_id"] = str(result.inserted_id)
    
    print(f"🔗 Blockchain: {transaction['_id']} | {tx_type} | ${amount} | Hash: 0x{current_hash[:8].upper()}")
    return transaction


async def verify_chain() -> dict:
    """Verify the entire blockchain by re-computing hashes"""
    txns = await db["transactions"].find().sort("timestamp", 1).to_list(length=1000)
    if not txns:
        return {"valid": True, "blocks": 0, "message": "Empty chain"}

    errors = []
    prev_hash = "0000000000000000"

    for i, tx in enumerate(txns):
        # Skip genesis if it exists but handled separately or just verify all
        raw = {
            "timestamp": tx["timestamp"],
            "from_id": tx["from_entity"]["id"],
            "to_id": tx["to_entity"]["id"],
            "amount": tx["amount"],
            "previous_hash": prev_hash,
            "task_id": tx.get("task_id") or "",
        }
        computed_hash = await calculate_hash(raw)
        actual_hash_part = tx["current_hash"].replace("0x", "").upper()
        if computed_hash[:16].upper() != actual_hash_part:
            errors.append(f"Block {tx['_id']}: Hash mismatch")
        prev_hash = computed_hash

    return {
        "valid": len(errors) == 0,
        "blocks": len(txns),
        "errors": errors,
        "message": "Chain verified" if not errors else f"{len(errors)} integrity errors found",
    }


async def get_ledger(limit: int = 50) -> list:
    """Get transactions from the ledger"""
    txns = await db["transactions"].find().sort("timestamp", -1).to_list(length=limit)
    for t in txns:
        t["_id"] = str(t["_id"])
    return txns


async def get_transaction(tx_id: str) -> Optional[dict]:
    """Find a specific transaction by ID"""
    tx = await db["transactions"].find_one({"_id": to_oid(tx_id)})
    if tx:
        tx["_id"] = str(tx["_id"])
    return tx


async def search_ledger(query: str) -> list:
    """Search transactions by student ID, company ID, or transaction ID"""
    search_query = {
        "$or": [
            {"type": {"$regex": query, "$options": "i"}},
            {"from_entity.id": {"$regex": query, "$options": "i"}},
            {"to_entity.id": {"$regex": query, "$options": "i"}},
            {"task_id": {"$regex": query, "$options": "i"}}
        ]
    }
    txns = await db["transactions"].find(search_query).to_list(length=100)
    for t in txns:
        t["_id"] = str(t["_id"])
    return txns
