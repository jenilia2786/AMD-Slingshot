"""Company Router — All company API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from database.connection import get_db, to_oid
from utils.auth_utils import company_required
from services.escrow_service import reserve_funds
from datetime import datetime

router = APIRouter(prefix="/api/company", tags=["Company"])
db = get_db()


@router.get("/profile")
async def get_profile(user: dict = Depends(company_required)):
    company = await db["companies"].find_one({"email": user["email"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company["_id"] = str(company["_id"])
    if "password" in company: del company["password"]
    
    return {"profile": company}


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(company_required)):
    company = await db["companies"].find_one({"email": user["email"]})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    company_id = str(company["_id"])
    active_tasks = await db["tasks"].find({"company_id": company_id, "status": "active"}).to_list(100)
    
    for t in active_tasks: 
        t["_id"] = str(t["_id"])
        # Count submissions for this task
        t["submissions_count"] = await db["submissions"].count_documents({"task_id": t["_id"]})
        
    return {
        "stats": {
            "active_tasks": len(active_tasks),
            "hired_candidates": company.get("hired_count", 0),
            "csr_balance": company.get("csr_balance", 0),
            "reserved_amount": company.get("reserved_amount", 0),
        },
        "active_tasks": active_tasks[:5],
        "company_type": company.get("type", "Corporate"),
        "logo_url": company.get("logo_url", "")
    }


@router.post("/create-task")
async def create_task(
    title: str, description: str, reward: int, 
    max_participants: int, deadline: str, 
    deliverables: str = "Code solution",
    tech_stack: str = "Python",
    min_score_threshold: int = 75,
    required_experience: str = "0-2 years",
    grad_year_start: int = 2022,
    grad_year_end: int = 2026,
    user: dict = Depends(company_required),
):
    company = await db["companies"].find_one({"email": user["email"]})
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    total_to_reserve = reward * max_participants
    
    # 1. Handle Escrow Reservation
    # This will raise 400 if insufficient funds
    await reserve_funds(str(company["_id"]), total_to_reserve, "NEW_TASK_RESERVE")

    new_task = {
        "company_id": str(company["_id"]),
        "company_name": company.get("name"),
        "title": title,
        "description": description,
        "deliverables": deliverables,
        "tech_stack": tech_stack,
        "reward_per_candidate": reward,
        "max_participants": max_participants,
        "deadline": deadline,
        "min_score": min_score_threshold,
        "eligibility_criteria": {
            "required_experience": required_experience,
            "min_skill_score": min_score_threshold,
            "grad_year_range": [grad_year_start, grad_year_end]
        },
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    result = await db["tasks"].insert_one(new_task)
    return {"task_id": str(result.inserted_id), "message": f"Task created. ${total_to_reserve} reserved in CSR escrow."}


@router.get("/candidates/{task_id}")
async def get_candidates(task_id: str, user: dict = Depends(company_required)):
    task = await db["tasks"].find_one({"_id": to_oid(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    submissions = await db["submissions"].find({"task_id": task_id}).to_list(100)
    
    candidates = []
    for s in submissions:
        student = await db["students"].find_one({"_id": to_oid(s["student_id"])})
        # Calculate eligibility status for UI
        criteria = task.get("eligibility_criteria", {})
        eligible = True
        reason = "Meets criteria"
        if student:
            if student.get("alumni_mode"):
                eligible = False
                reason = "Alumni Mode"
            elif criteria:
                grad_range = criteria.get("grad_year_range", [])
                if grad_range and (student.get("graduation_year") < grad_range[0] or student.get("graduation_year") > grad_range[1]):
                    eligible = False
                    reason = f"Grad Year ({student.get('graduation_year')}) outside range"
        
        ai_eval = s.get("ai_evaluation", {})
        
        candidates.append({
            "submission_id": str(s["_id"]),
            "student_id": s["student_id"],
            "name": student.get("name", "Unknown") if student else "Unknown",
            "college": student.get("college", "N/A") if student else "N/A",
            "grad_year": student.get("graduation_year", "N/A") if student else "N/A",
            "ai_score": ai_eval.get("overall_score", 0),
            "plagiarism_risk": ai_eval.get("plagiarism_risk", 0),
            "recommendation": ai_eval.get("hiring_recommendation", "N/A"),
            "skills": ai_eval.get("extracted_skills", []),
            "status": s.get("status"),
            "is_eligible": eligible,
            "eligibility_reason": reason,
            "github_url": s.get("github_url"),
            "zip_path": s.get("zip_path")
        })
    candidates.sort(key=lambda x: x["ai_score"], reverse=True)
    return {"candidates": candidates}

@router.get("/csr-wallet")
async def get_csr_wallet(user: dict = Depends(company_required)):
    company = await db["companies"].find_one({"email": user["email"]})
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    txns = await db["transactions"].find({"company_id": str(company["_id"])}).sort("timestamp", -1).to_list(20)
    for t in txns:
        t["_id"] = str(t["_id"])
        
    balance = company.get("csr_balance", 0)
    reserved = company.get("reserved_amount", 0)
    return {
        "total_balance": balance + reserved,
        "available": balance,
        "escrow_locked": reserved,
        "transactions": txns
    }

@router.post("/allocate-sponsorship")
async def allocate_sponsorship(startup_id: str, amount: int, user: dict = Depends(company_required)):
    """Corporate allocates Reward pools to a Startup Pool."""
    corporate = await db["companies"].find_one({"_id": to_oid(user["user_id"])})
    if not corporate or corporate.get("csr_balance", 0) < amount:
         raise HTTPException(status_code=400, detail="Insufficient CSR balance for sponsorship.")

    # Deduct from Corporate
    await db["companies"].update_one(
        {"_id": corporate["_id"]},
        {"$inc": {"csr_balance": -amount}}
    )

    # Credit Startup CSR Balance (Auditable)
    await db["companies"].update_one(
        {"_id": to_oid(startup_id)},
        {"$inc": {"csr_balance": amount}}
    )

    # Log
    await db["transactions"].insert_one({
        "type": "SPONSORSHIP",
        "from_corporate": user["user_id"],
        "to_startup": startup_id,
        "amount": amount,
        "timestamp": datetime.now().isoformat()
    })

    return {"success": True, "message": f"Allocated ${amount} to startup internship pool."}

