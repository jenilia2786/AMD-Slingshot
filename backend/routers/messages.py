from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.connection import get_db, to_oid
from utils.auth_utils import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/messages", tags=["Internal Messaging"])
db = get_db()

class MessageSend(BaseModel):
    receiver_id: str
    content: str

@router.get("/{other_id}")
async def get_messages(other_id: str, user: dict = Depends(get_current_user)):
    """Fetch chat history between two users if they are mentor-student pair"""
    # Verify relationship
    current_id = user["user_id"]
    
    # Check if mentor-student pair exists in mentorships
    rel = await db["mentorships"].find_one({
        "$or": [
            {"mentor_id": current_id, "student_id": other_id},
            {"mentor_id": other_id, "student_id": current_id}
        ]
    })
    
    if not rel:
        raise HTTPException(status_code=403, detail="You can only chat with your assigned mentor/student")
        
    messages = await db["messages"].find({
        "$or": [
            {"sender_id": current_id, "receiver_id": other_id},
            {"sender_id": other_id, "receiver_id": current_id}
        ]
    }).sort("timestamp", 1).to_list(100)
    
    for m in messages: m["_id"] = str(m["_id"])
    return {"messages": messages}

@router.post("/")
async def send_message(req: MessageSend, user: dict = Depends(get_current_user)):
    """Send a message to assigned peer"""
    current_id = user["user_id"]
    
    # Verify relationship
    rel = await db["mentorships"].find_one({
        "$or": [
            {"mentor_id": current_id, "student_id": req.receiver_id},
            {"mentor_id": req.receiver_id, "student_id": current_id}
        ]
    })
    
    if not rel:
        raise HTTPException(status_code=403, detail="Messaging only allowed with assigned mentor/student")
        
    # Prevent financial keywords
    forbidden = ["money", "payment", "bank", "account", "transfer", "escrow", "funds", "salary", "stipend"]
    if any(word in req.content.lower() for word in forbidden):
        raise HTTPException(status_code=400, detail="Financial discussions are prohibited in this chat. Please use official channels.")
        
    new_msg = {
        "sender_id": current_id,
        "receiver_id": req.receiver_id,
        "content": req.content,
        "timestamp": datetime.now().isoformat()
    }
    await db["messages"].insert_one(new_msg)
    return {"message": "Sent"}
