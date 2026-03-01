from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.connection import get_db, to_oid
from utils.auth_utils import student_required, mentor_required, get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/mentorship", tags=["Mentorship"])
db = get_db()

class RequestResponse(BaseModel):
    request_id: str
    action: str # 'accept' or 'reject'

@router.get("/mentors")
async def get_mentors(user: dict = Depends(student_required)):
    """Allow students to browse verified mentors"""
    mentors = await db["mentors"].find({"verified_company_email": True}).to_list(100)
    
    # Check if student already requested
    student_id = user["user_id"]
    requests = await db["mentorship_requests"].find({"student_id": student_id}).to_list(100)
    request_map = {r["mentor_id"]: r["status"] for r in requests}
    
    result = []
    for m in mentors:
        m_id = str(m["_id"])
        result.append({
            "id": m_id,
            "name": m.get("name"),
            "domain": m.get("domain"),
            "experience": m.get("experience_years"),
            "status": request_map.get(m_id, "none") # none, pending, accepted, rejected
        })
    return {"mentors": result}

@router.post("/request/{mentor_id}")
async def request_mentorship(mentor_id: str, user: dict = Depends(student_required)):
    """Student requests a mentor"""
    student = await db["students"].find_one({"_id": to_oid(user["user_id"])})
    if student.get("alumni_mode"):
        raise HTTPException(status_code=403, detail="Alumni cannot request new mentorship")
        
    # Check if already requested
    existing = await db["mentorship_requests"].find_one({
        "student_id": user["user_id"],
        "mentor_id": mentor_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Request already sent")
        
    new_request = {
        "student_id": user["user_id"],
        "mentor_id": mentor_id,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }
    await db["mentorship_requests"].insert_one(new_request)
    return {"message": "Mentorship request sent"}

@router.get("/requests")
async def get_requests(user: dict = Depends(mentor_required)):
    """Mentor views incoming requests"""
    requests = await db["mentorship_requests"].find({
        "mentor_id": user["user_id"],
        "status": "pending"
    }).to_list(100)
    
    result = []
    for r in requests:
        student = await db["students"].find_one({"_id": to_oid(r["student_id"])})
        if student:
            result.append({
                "request_id": str(r["_id"]),
                "student_id": r["student_id"],
                "student_name": student.get("name"),
                "college": student.get("college"),
                "grad_year": student.get("graduation_year"),
                "skills": student.get("skills", []),
                "readiness_index": student.get("readiness_index"),
                "timestamp": r["timestamp"]
            })
    return {"requests": result}

@router.post("/respond")
async def respond_to_request(req: RequestResponse, user: dict = Depends(mentor_required)):
    """Mentor accepts or rejects student"""
    request = await db["mentorship_requests"].find_one({"_id": to_oid(req.request_id)})
    if not request or request["mentor_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if req.action == "accept":
        await db["mentorship_requests"].update_one(
            {"_id": to_oid(req.request_id)},
            {"$set": {"status": "accepted"}}
        )
        # Add to mentorships mapping
        mentorship = {
            "mentor_id": user["user_id"],
            "student_id": request["student_id"],
            "assigned_at": datetime.now().isoformat()
        }
        await db["mentorships"].insert_one(mentorship)
        
        # Log assignment
        await db["audit_logs"].insert_one({
            "type": "MENTORSHIP_ASSIGNED",
            "mentor_id": user["user_id"],
            "student_id": request["student_id"],
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": "Student accepted. Internal chat is now enabled."}
    else:
        await db["mentorship_requests"].update_one(
            {"_id": to_oid(req.request_id)},
            {"$set": {"status": "rejected"}}
        )
        return {"message": "Request rejected"}

@router.get("/interns")
async def get_interns(user: dict = Depends(mentor_required)):
    """Mentor views accepted students"""
    mentorships = await db["mentorships"].find({"mentor_id": user["user_id"]}).to_list(100)
    
    result = []
    for m in mentorships:
        student = await db["students"].find_one({"_id": to_oid(m["student_id"])})
        if student:
            result.append({
                "student_id": m["student_id"],
                "name": student.get("name"),
                "college": student.get("college"),
                "skills": student.get("skills", []),
                "assigned_at": m["assigned_at"]
            })
    return {"interns": result}
