from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────
class ApplicationStatus(str, Enum):
    Applied = "Applied"
    Shortlisted = "Shortlisted"
    Rejected = "Rejected"
    Scheduled = "Scheduled"
    Interviewed = "Interviewed"


class JobStatus(str, Enum):
    Active = "Active"
    Closed = "Closed"
    Draft = "Draft"


# ── User ──────────────────────────────────────────────
class UserBase(BaseModel):
    email: str
    full_name: str
    role: str


class UserCreate(UserBase):
    clerk_id: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None


class UserOut(UserBase):
    id: int
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: str


# ── Company ───────────────────────────────────────────
class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None


class CompanyCreate(CompanyBase):
    logo_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyOut(CompanyBase):
    id: int
    logo_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Job ───────────────────────────────────────────────
class JobBase(BaseModel):
    title: str
    description: str
    company: str
    location: Optional[str] = None


class JobCreate(JobBase):
    job_type: str = "Full Time"
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    skills_required: Optional[List[str]] = None


class JobOut(JobBase):
    id: int
    job_type: str
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    skills_required: Optional[List[str]] = None
    status: str
    is_open: bool
    created_at: datetime
    recruiter_id: int
    applicant_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Application ───────────────────────────────────────
class ApplicationBase(BaseModel):
    job_id: int


class ApplicationCreate(ApplicationBase):
    notice_period: Optional[str] = None
    current_ctc: Optional[str] = None
    latest_company: Optional[str] = None
    cover_letter: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationOut(ApplicationBase):
    id: int
    candidate_id: int
    status: str
    notice_period: Optional[str] = None
    current_ctc: Optional[str] = None
    latest_company: Optional[str] = None
    ai_score: Optional[float] = None
    applied_at: datetime

    class Config:
        from_attributes = True


# ── Assessment ────────────────────────────────────────
class AssessmentCreate(BaseModel):
    job_id: int
    name: str
    assessment_type: str
    num_questions: int = 10
    duration_minutes: int = 30
    due_date: Optional[datetime] = None
    prompt_used: Optional[str] = None


class AssessmentOut(BaseModel):
    id: int
    job_id: int
    name: str
    assessment_type: str
    num_questions: int
    duration_minutes: int
    due_date: Optional[datetime] = None
    questions_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Interview ─────────────────────────────────────────
class InterviewCreate(BaseModel):
    application_id: int
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 30


class InterviewOut(BaseModel):
    id: int
    application_id: int
    scheduled_at: Optional[datetime] = None
    duration_minutes: int
    status: str
    score: Optional[float] = None
    ai_notes: Optional[str] = None
    transcript_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard Stats ───────────────────────────────────
class DashboardStats(BaseModel):
    jobs_posted: int
    total_applications: int
    shortlisted: int
    rejected: int
    recent_jobs: List[JobOut]
