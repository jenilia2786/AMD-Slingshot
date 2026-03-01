"""Pydantic models for AccelerateAI"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    student = "student"
    company = "company"
    government = "government"


class UserBase(BaseModel):
    email: str
    role: Role
    name: str


class StudentCreate(BaseModel):
    email: str
    password: str
    name: str
    college: str
    branch: str
    nm_id: Optional[str] = None


class CompanyCreate(BaseModel):
    email: str
    password: str
    name: str
    type: str  # Corporate, Startup


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


class TaskCreate(BaseModel):
    title: str
    description: str
    skills_required: List[str]
    difficulty: str
    reward_per_candidate: int = Field(ge=200, le=1000)
    internship_stipend: int = Field(ge=1000)  # MANDATORY
    max_participants: int = Field(ge=1, le=50)
    deadline: str
    task_type: str = "Code"
    work_mode: str = "Remote"
    internship_duration: str = "3 months"
    domain: Optional[str] = None


class SubmissionCreate(BaseModel):
    task_id: str
    code: str
    language: str = "Python"
    github_url: Optional[str] = None
    zip_path: Optional[str] = None
    approach: Optional[str] = None


class WithdrawRequest(BaseModel):
    amount: int
    upi_id: str


class DepositRequest(BaseModel):
    amount: int


class SelectCandidateRequest(BaseModel):
    student_id: str
    task_id: str
    offer_details: dict


class RejectCandidateRequest(BaseModel):
    student_id: str
    task_id: str
    reason: str
    feedback: Optional[str] = None


class FlagCompanyRequest(BaseModel):
    company_id: str
    reason: str
    action: str
    notes: Optional[str] = None


class EvaluationRequest(BaseModel):
    submission_id: str
    code: str
    task_requirements: str
    student_id: Optional[str] = None
