from fastapi import APIRouter, Depends, HTTPException
from database.connection import get_db, to_oid
from utils.auth_utils import student_required
from datetime import datetime
import random

router = APIRouter(prefix="/api/test", tags=["Skill Test"])
db = get_db()

@router.get("/questions")
async def get_questions(domain: str = "General"):
    """Get 25 randomized questions for a specific domain."""
    # In a real app, this pulls from a large DB. For hackathon, we assume a collection 'question_bank'.
    questions = await db["question_bank"].find({"domain": domain}).to_list(100)
    if len(questions) < 25:
        # Fallback to some default questions if bank is empty
        return {"questions": questions} 
    
    selected = random.sample(questions, 25)
    for q in selected: q["_id"] = str(q["_id"])
    return {"questions": selected}

@router.post("/submit")
async def submit_test(
    domain: str, 
    score: int, 
    tab_switches: int, 
    user: dict = Depends(student_required)
):
    """Submit test result with integrity check."""
    if tab_switches > 2:
        return {
            "status": "flagged", 
            "message": "Test invalidated due to excessive tab switching (Integrity Violation)."
        }
    
    test_result = {
        "student_id": user["user_id"],
        "domain": domain,
        "score": score,
        "tab_switches": tab_switches,
        "status": "verified" if tab_switches <= 2 else "flagged",
        "timestamp": datetime.now().isoformat()
    }
    
    # We don't save to profile yet, we return the result and ask the user (frontend logic)
    # The requirement says: After test completion, Ask: "Do you want to add this verified score to your profile?"
    # So we return a temporary ID or the data.
    result = await db["temp_test_results"].insert_one(test_result)
    return {
        "temp_id": str(result.inserted_id),
        "score": score,
        "status": test_result["status"],
        "message": "Test completed. Would you like to add this to your verified profile?"
    }

@router.post("/confirm/{temp_id}")
async def confirm_test(temp_id: str, save: bool, user: dict = Depends(student_required)):
    """Add verified score to profile or discard."""
    if not save:
        await db["temp_test_results"].delete_one({"_id": to_oid(temp_id)})
        return {"message": "Score discarded."}
    
    temp = await db["temp_test_results"].find_one({"_id": to_oid(temp_id), "student_id": user["user_id"]})
    if not temp:
        raise HTTPException(status_code=404, detail="Test result not found.")
    
    # Add to student profile
    await db["students"].update_one(
        {"_id": to_oid(user["user_id"])},
        {"$push": {"certified_scores": {
            "domain": temp["domain"],
            "score": temp["score"],
            "date": temp["timestamp"],
            "integrity": temp["status"]
        }}}
    )
    
    await db["temp_test_results"].delete_one({"_id": to_oid(temp_id)})
    return {"message": "Score added to profile successfully."}
