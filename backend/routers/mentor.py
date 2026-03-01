from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from database.connection import get_db, to_oid
from utils.auth_utils import mentor_required
from datetime import datetime

router = APIRouter(prefix="/api/mentor", tags=["Mentor"])
db = get_db()

@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(mentor_required)):
    mentor = await db["mentors"].find_one({"_id": to_oid(user["user_id"])})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
        
    # Assigned interns (Task-based)
    task_assignments = await db["mentor_assignments"].find({"mentor_id": user["user_id"]}).to_list(length=100)
    
    # Guidance interns (Mentorship-based)
    guidance_mentorships = await db["mentorships"].find({"mentor_id": user["user_id"]}).to_list(length=100)
    
    interns = []
    # Process Task-based
    for a in task_assignments:
        student = await db["students"].find_one({"_id": to_oid(a["student_id"])})
        task = await db["tasks"].find_one({"_id": to_oid(a["task_id"])})
        if student and task:
            interns.append({
                "student_id": a["student_id"],
                "name": student.get("name"),
                "task_title": task.get("title"),
                "type": "Task Guidance",
                "joined_at": a.get("created_at")
            })
    
    # Process Guidance-based
    for m in guidance_mentorships:
        student = await db["students"].find_one({"_id": to_oid(m["student_id"])})
        if student:
            interns.append({
                "student_id": m["student_id"],
                "name": student.get("name"),
                "task_title": "Academic Mentorship",
                "type": "Mentorship",
                "joined_at": m.get("assigned_at")
            })

    return {
        "stats": {
            "assigned_interns": len(interns),
            "pending_feedback": len([i for i in interns if not i.get("feedback_given")]),
            "hours_mentored": mentor.get("hours_mentored", 0),
            "honorarium_balance": mentor.get("wallet_balance", 0)
        },
        "interns": interns,
        "profile": {
            "name": mentor.get("name"),
            "domain": mentor.get("domain"),
            "verified": mentor.get("verified_company_email", False)
        }
    }

@router.post("/submit-feedback")
async def submit_feedback(
    student_id: str, task_id: str, feedback_text: str, 
    performance_level: str, user: dict = Depends(mentor_required)
):
    feedback_data = {
        "mentor_id": user["user_id"],
        "student_id": student_id,
        "task_id": task_id,
        "feedback_text": feedback_text,
        "performance_level": performance_level, # Exceptional, Good, Average
        "created_at": datetime.now().isoformat()
    }
    
    await db["mentor_feedback"].insert_one(feedback_data)
    
    # Mock honorarium release (increment mentor balance)
    await db["mentors"].update_one(
        {"_id": to_oid(user["user_id"])},
        {"$inc": {"wallet_balance": 500, "hours_mentored": 2}}
    )
    
    return {"message": "Feedback submitted. $500 honorarium added to your wallet."}

@router.get("/wallet")
async def get_wallet(user: dict = Depends(mentor_required)):
    mentor = await db["mentors"].find_one({"_id": to_oid(user["user_id"])})
    
    payments = await db["mentor_payments"].find({"mentor_id": user["user_id"]}).to_list(length=20)
    for p in payments:
        p["_id"] = str(p["_id"])
    
    return {
        "balance": mentor.get("wallet_balance", 0),
        "history": payments
    }
