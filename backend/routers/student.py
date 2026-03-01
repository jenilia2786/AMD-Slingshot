from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile
from typing import Optional
from database.connection import get_db, to_oid
from utils.auth_utils import student_required
from services.crew_ai_service import run_evaluation, run_resume_analysis
from models.user import SubmissionCreate
from datetime import datetime
import io
import PyPDF2

router = APIRouter(prefix="/api/student", tags=["Student"])
db = get_db()


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(student_required)):
    student = await db["students"].find_one({"email": user["email"]})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    tasks = await db["tasks"].find({"status": "active"}).to_list(length=100)
    for t in tasks:
        t["_id"] = str(t["_id"])
    
    return {
        "stats": {
            "available_tasks": len(tasks),
            "completed_tasks": student.get("completed_tasks", 0),
            "total_earnings": student.get("wallet_balance", 0),
            "pending_evaluations": student.get("pending_evaluations", 0),
        },
        "eligibility": {
            "is_alumni": student.get("alumni_mode", False),
            "grad_year": student.get("graduation_year"),
            "status": "Alumni Mode" if student.get("alumni_mode") else "Eligible"
        },
        "available_tasks": tasks[:6],
        "wallet_balance": student.get("wallet_balance", 0),
    }


@router.get("/tasks")
async def get_tasks(
    domain: Optional[str] = None,
    skill_level: Optional[str] = None,
    reward_min: Optional[int] = None,
    reward_max: Optional[int] = None,
    company_type: Optional[str] = None,
    user: dict = Depends(student_required),
):
    query = {"status": "active"}
    
    if domain:
        query["domain"] = {"$regex": domain, "$options": "i"}
    if skill_level:
        query["difficulty"] = skill_level
    if reward_min or reward_max:
        query["reward_per_candidate"] = {}
        if reward_min:
            query["reward_per_candidate"]["$gte"] = reward_min
        if reward_max:
            query["reward_per_candidate"]["$lte"] = reward_max
    if company_type:
        query["company_type"] = company_type
        
    tasks = await db["tasks"].find(query).to_list(length=100)
    for t in tasks:
        t["_id"] = str(t["_id"])
    return {"tasks": tasks, "count": len(tasks)}




async def perform_ai_eval(submission_id: str, code: str, task_details: dict, task_id: str, student_id: str):
    try:
        # Run detailed LLM evaluation
        result = await run_evaluation(submission_id, code, task_details)
        eval_data = result["evaluation"]
        score = eval_data.get("overall_score", 0)
        
        # Get task threshold
        task = await db["tasks"].find_one({"_id": to_oid(task_id)})
        threshold = task.get("min_score", 70)
        company_id = task.get("company_id")
        
        status = "evaluated"
        payment_status = "pending"
        
        # 1. Update submission first
        await db["submissions"].update_one(
            {"_id": to_oid(submission_id)},
            {
                "$set": {
                    "ai_evaluation": eval_data,
                    "status": status,
                    "evaluated_at": datetime.now().isoformat()
                }
            }
        )

        # 2. Score check for Reward Release
        if score >= threshold and not eval_data.get("plagiarism_risk", 0) > 40:
            from services.escrow_service import release_reward
            try:
                reward_amount = task.get("reward_per_candidate", 800)
                await release_reward(task_id, student_id, company_id, reward_amount)
                # Mark submission as reward_released
                await db["submissions"].update_one(
                    {"_id": to_oid(submission_id)},
                    {"$set": {"status": "reward_released", "payment_status": "released"}}
                )
            except Exception as e:
                print(f"💰 Reward release error: {e}")

        # 3. Update student skill tags
        await db["students"].update_one(
            {"_id": to_oid(student_id)},
            {"$addToSet": {"skills": {"$each": eval_data.get("extracted_skills", [])}}}
        )
        
    except Exception as e:
        print(f"❌ Background evaluation error: {e}")


@router.post("/submit-task")
async def submit_task(
    submission: SubmissionCreate, 
    background_tasks: BackgroundTasks, 
    user: dict = Depends(student_required),
):
    task_id = submission.task_id
    code = submission.code
    github_url = submission.github_url
    zip_path = submission.zip_path
    language = submission.language or "Python"
    approach = submission.approach

    task = await db["tasks"].find_one({"_id": to_oid(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    student = await db["students"].find_one({"_id": to_oid(user["user_id"])})
    
    # 1. Alumni Mode Check
    if student.get("alumni_mode"):
        raise HTTPException(status_code=403, detail="Alumni cannot apply for new internships. You are in Alumni Mode.")

    # 2. Eligibility Criteria Check
    criteria = task.get("eligibility_criteria", {})
    if criteria:
        # Grad Year Check
        grad_range = criteria.get("grad_year_range", [])
        if grad_range and (student.get("graduation_year") < grad_range[0] or student.get("graduation_year") > grad_range[1]):
            raise HTTPException(status_code=403, detail=f"Your graduation year ({student.get('graduation_year')}) is outside the required range.")

        # Skill Score Check
        min_score = criteria.get("min_skill_score", 0)
        best_score = max([c.get("score", 0) for c in student.get("certified_scores", [])] + [student.get("readiness_index", 0)])
        if best_score < min_score:
            raise HTTPException(status_code=403, detail=f"Minimum skill score of {min_score} required. Your best score is {best_score}.")

    # Anti-exploitation demo limit: max 10 submissions per company
    existing = await db["submissions"].find({"student_id": user["user_id"], "company_id": task["company_id"]}).to_list(100)
    if len(existing) >= 10:
        raise HTTPException(status_code=400, detail="Max 10 submissions allowed per company for this demo.")

    new_submission = {
        "student_id": user["user_id"],
        "student_email": user["email"],
        "task_id": task_id,
        "company_id": task["company_id"],
        "code": code,
        "github_url": github_url,
        "zip_path": zip_path,
        "language": language,
        "status": "pending_evaluation",
        "timestamp": datetime.now().isoformat()
    }
    
    result = await db["submissions"].insert_one(new_submission)
    submission_id = str(result.inserted_id)
    
    # Task context for LLM
    task_details = {
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "deliverables": task.get("deliverables", "Complete code solution"),
        "tech_stack": task.get("tech_stack", "General Python/Web"),
        "rubric": f"Score 100 if perfect, threshold is {task.get('min_score', 70)}"
    }

    background_tasks.add_task(perform_ai_eval, submission_id, code, task_details, task_id, user["user_id"])
    
    return {
        "submission_id": submission_id,
        "message": "Task submitted. Real AI evaluation queued.",
        "estimated_time": "45-60 seconds"
    }


@router.post("/portfolio/add-project")
async def add_portfolio_project(
    title: str, github_url: str, zip_path: Optional[str] = None,
    user: dict = Depends(student_required)
):
    """Add a self-added project to student portfolio."""
    student = await db["students"].find_one({"_id": to_oid(user["user_id"])})
    if student.get("alumni_mode"):
        raise HTTPException(status_code=403, detail="Alumni cannot add new projects for evaluation.")
    project = {
        "student_id": user["user_id"],
        "title": title,
        "github_url": github_url,
        "zip_path": zip_path,
        "type": "self-added",
        "evaluation_status": "pending",
        "created_at": datetime.now().isoformat()
    }
    result = await db["portfolio"].insert_one(project)
    return {"project_id": str(result.inserted_id), "message": "Project added to portfolio."}


@router.post("/portfolio/evaluate/{project_id}")
async def evaluate_portfolio_project(project_id: str, code: str, user: dict = Depends(student_required)):
    """Trigger AI evaluation for a portfolio project (No payment)."""
    project = await db["portfolio"].find_one({"_id": to_oid(project_id), "student_id": user["user_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from services.crew_ai_service import run_project_evaluation
    result = await run_project_evaluation(project["title"], code, project["github_url"])
    
    await db["portfolio"].update_one(
        {"_id": to_oid(project_id)},
        {"$set": {"ai_evaluation": result, "evaluation_status": "completed"}}
    )
    return result

@router.get("/portfolio")
async def get_portfolio(user: dict = Depends(student_required)):
    # 1. Get self-added projects
    projects = await db["portfolio"].find({"student_id": user["user_id"]}).to_list(100)
    # 2. Get task-based submissions that are completed
    submissions = await db["submissions"].find({
        "student_id": user["user_id"], 
        "status": {"$in": ["evaluated", "reward_released"]}
    }).to_list(100)
    
    # Format
    items = []
    for p in projects:
        items.append({
            "id": str(p["_id"]),
            "title": p["title"],
            "type": "Self-Project",
            "github": p["github_url"],
            "score": p.get("ai_evaluation", {}).get("score", "N/A"),
            "skills": p.get("ai_evaluation", {}).get("skills_demonstrated", []),
            "date": p["created_at"]
        })
        
    for s in submissions:
        # Find task details
        task = await db["tasks"].find_one({"_id": to_oid(s["task_id"])})
        items.append({
            "id": str(s["_id"]),
            "title": task.get("title", "Task Submission") if task else "Task Submission",
            "type": "Internship Task",
            "github": s["github_url"],
            "score": s.get("ai_evaluation", {}).get("overall_score", 0),
            "skills": s.get("ai_evaluation", {}).get("extracted_skills", []),
            "date": s.get("timestamp", s.get("evaluated_at", ""))
        })
        
    return {"portfolio": items}


@router.get("/evaluation/{submission_id}")
async def get_evaluation(submission_id: str, user: dict = Depends(student_required)):
    submission = await db["submissions"].find_one({"_id": to_oid(submission_id)})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission.get("ai_evaluation", {"status": "pending"})


@router.get("/wallet")
async def get_wallet(user: dict = Depends(student_required)):
    student = await db["students"].find_one({"_id": to_oid(user["user_id"])})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Filter transactions where this student is the target
    txns = await db["transactions"].find({
        "$or": [
            {"student_id": user["user_id"]},
            {"to_entity.id": user["user_id"]}
        ]
    }).sort("timestamp", -1).to_list(100)
    
    for t in txns: t["_id"] = str(t["_id"])
    
    # Calculate totals
    total_withdrawn = sum(abs(t["amount"]) for t in txns if t["type"] == "withdrawal")
    
    # Pending evaluation value from submissions
    pending_submissions = await db["submissions"].find({
        "student_id": user["user_id"],
        "status": "pending"
    }).to_list(100)
    pending_value = sum(s.get("reward_amount", 0) for s in pending_submissions)

    return {
        "balance": student.get("wallet_balance", 0),
        "total_earned": student.get("total_earned", 0),
        "total_withdrawn": total_withdrawn,
        "pending_evaluations_value": pending_value,
        "transactions": txns
    }


@router.get("/profile")
async def get_profile(user: dict = Depends(student_required)):
    student = await db["students"].find_one({"email": user["email"]})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    safe = {k: v for k, v in student.items() if k not in ["password", "password_hash"]}
    safe["_id"] = str(safe["_id"])
    
    # Calculate weighted readiness or just pull from DB saved via Resume Analysis
    return {"profile": safe, "readiness_index": student.get("readiness_index", 75)}

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), user: dict = Depends(student_required)):
    contents = await file.read()
    resume_text = ""
    # Extract PDF text
    if file.filename.endswith(".pdf"):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(contents))
            for page in reader.pages: resume_text += page.extract_text() or ""
        except Exception: resume_text = f"Resume analysis request for {file.filename}."
    else: resume_text = str(contents[:5000])

    result = await run_resume_analysis(resume_text)
    
    # Update readiness and extracted skills
    await db["students"].update_one(
        {"_id": to_oid(user["user_id"])},
        {"$set": {
            "readiness_index": result.get("readiness_index", 75),
            "resume_skills": result.get("extracted_skills", [])
        }}
    )
    return result

@router.get("/role-suggestions")
async def get_role_suggestions(user: dict = Depends(student_required)):
    student = await db["students"].find_one({"_id": to_oid(user["user_id"])})
    if not student: raise HTTPException(status_code=404, detail="Student not found")

    from services.crew_ai_service import run_role_suggestion
    # Collect skills from all sources
    all_skills = list(set(student.get("skills", []) + student.get("resume_skills", [])))
    
    # Collect test scores
    certs = student.get("certified_scores", [])
    scores = [c["score"] for c in certs] if certs else [70] # Mock default if none
    
    roles = await run_role_suggestion(all_skills, scores, student.get("resume_skills", []))
    return {"suggested_roles": roles}

