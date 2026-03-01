"""
AI Evaluation Router — CrewAI Multi-Agent System
4 agents: Technical Evaluator, Plagiarism Detector, Resume Analyzer, Fraud Synthesizer
"""
from fastapi import APIRouter, Depends, HTTPException
from database.connection import get_db, to_oid
from utils.auth_utils import get_current_user
from services.crew_ai_service import run_evaluation
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["AI Evaluation"])
db = get_db()


@router.post("/evaluate")
async def evaluate_submission(
    submission_id: str,
    code: str,
    task_requirements: str,
    student_id: str = None,
    user: dict = Depends(get_current_user),
):
    """Run CrewAI multi-agent evaluation on a student submission and save to MongoDB"""
    # Run evaluation
    result = await run_evaluation(
        submission_id=submission_id,
        code=code,
        task_requirements=task_requirements,
        student_id=student_id,
    )
    
    # Save result to MongoDB
    # We store the result in the 'submissions' collection
    await db["submissions"].update_one(
        {"_id": to_oid(submission_id)},
        {
            "$set": {
                "ai_evaluation": result.get("final_result"),
                "status": "evaluated",
                "evaluation_method": "crewai_real",
                "evaluated_at": datetime.now().isoformat()
            }
        },
        upsert=True # In case submission record doesn't exist yet
    )
    
    return result


@router.get("/evaluation-status/{submission_id}")
async def get_evaluation_status(submission_id: str, user: dict = Depends(get_current_user)):
    submission = await db["submissions"].find_one({"_id": to_oid(submission_id)})
    if not submission:
        return {
            "submission_id": submission_id,
            "status": "not_found",
            "message": "Submission not found in database"
        }
        
    return {
        "submission_id": submission_id,
        "status": submission.get("status", "pending"),
        "agents_completed": ["technical", "plagiarism", "resume", "fraud"] if submission.get("status") == "evaluated" else [],
        "message": "CrewAI evaluation status retrieved from MongoDB"
    }
