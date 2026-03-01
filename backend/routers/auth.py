"""Authentication Router — Login for all user roles"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database.connection import get_db, to_oid
from utils.jwt_handler import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
db = get_db()

# --- Models ---
class LoginRequest(BaseModel):
    email: str
    password: str
    role: str

class CompanyRegisterRequest(BaseModel):
    company_name: str
    email: str
    password: str
    company_type: str
    industry_domain: str = "Technology"
    logo_url: str = "../assets/tn-logo.png"

class StudentRegisterRequest(BaseModel):
    name: str
    email: str # Personal email
    password: str
    college_name: str
    college_email: str
    graduation_year: int
    degree: str
    branch: str
    resume_url: str = ""
    github_profile: str = ""

class MentorRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    linkedin_url: str
    company_email: str
    experience_years: int
    domain: str

# --- Endpoints ---

@router.post("/login")
async def login(req: LoginRequest):
    """Login endpoint for all roles"""
    collection_map = {
        "student": "students",
        "company": "companies",
        "government": "government",
        "mentor": "mentors"
    }
    collection_name = collection_map.get(req.role)
    if not collection_name:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await db[collection_name].find_one({"email": req.email})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    token_data = {"user_id": str(user["_id"]), "email": user["email"], "role": req.role}
    token = create_access_token(token_data)

    safe_user = {k: v for k, v in user.items() if k not in ["password", "password_hash"]}
    safe_user["_id"] = str(safe_user["_id"])
    safe_user["role"] = req.role

    return {"token": token, "user": safe_user}


@router.post("/register/company")
async def register_company(req: CompanyRegisterRequest):
    existing = await db["companies"].find_one({"email": req.email})
    if existing: raise HTTPException(status_code=400, detail="Email exists")
    
    new_company = {
        "name": req.company_name,
        "email": req.email,
        "password": req.password,
        "type": req.company_type, # Standardized 'type'
        "industry_domain": req.industry_domain,
        "logo_url": req.logo_url,
        "role": "company",
        "status": "pending",
        "csr_balance": 0,
        "reserved_amount": 0,
        "hired_count": 0, # Added counter
        "trust_score": 4.0,
        "verified_status": False,
        "created_at": datetime.now().isoformat()
    }
    result = await db["companies"].insert_one(new_company)
    return {"message": "Company registered", "id": str(result.inserted_id)}


@router.post("/register/student")
async def register_student(req: StudentRegisterRequest):
    existing = await db["students"].find_one({"email": req.email})
    if existing: raise HTTPException(status_code=400, detail="Email exists")
    
    # --- Eligibility Logic ---
    current_year = datetime.now().year
    # alumni_mode = True if current_year > graduation_year + 2
    alumni_mode = current_year > req.graduation_year + 2
    
    new_student = {
        "name": req.name,
        "email": req.email,
        "password": req.password,
        "college_name": req.college_name,
        "college_email": req.college_email,
        "graduation_year": req.graduation_year,
        "degree": req.degree,
        "branch": req.branch,
        "alumni_mode": alumni_mode,
        "resume_url": req.resume_url,
        "github_profile": req.github_profile,
        "role": "student",
        "wallet_balance": 0,
        "total_earned": 0,
        "readiness_index": 78,
        "created_at": datetime.now().isoformat()
    }
    result = await db["students"].insert_one(new_student)
    return {"message": "Student registered", "id": str(result.inserted_id)}


@router.post("/register/mentor")
async def register_mentor(req: MentorRegisterRequest):
    existing = await db["mentors"].find_one({"email": req.email})
    if existing: raise HTTPException(status_code=400, detail="Email exists")
    
    new_mentor = {
        "name": req.name,
        "email": req.email,
        "password": req.password,
        "linkedin_url": req.linkedin_url,
        "company_email": req.company_email,
        "experience_years": req.experience_years,
        "domain": req.domain,
        "role": "mentor",
        "verified_linkedin": False,
        "verified_company_email": False,
        "wallet_balance": 0,
        "created_at": datetime.now().isoformat()
    }
    result = await db["mentors"].insert_one(new_mentor)
    return {"message": "Mentor registered", "id": str(result.inserted_id)}


@router.get("/verify")
async def verify_token(token: str):
    from utils.jwt_handler import get_user_from_token
    user = get_user_from_token(token)
    if not user: raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True, "user": user}
