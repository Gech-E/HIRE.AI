from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from fastapi.security import HTTPAuthorizationCredentials
import models
import schemas
from auth import get_current_user, require_auth, verify_token, auth_scheme

app = FastAPI(
    title="Hire.ai Platform API",
    description="API for the AI-powered recruiting platform",
    version="1.0.0",
)

# Locked CORS — only allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Hire.ai Backend API!"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(func.now())
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


# ── Users ──────────────────────────────────────────────
@app.post("/api/users/sync")
def sync_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")

    payload = verify_token(credentials.credentials)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.clerk_id == clerk_id).first()
    if not user:
        user = models.User(
            clerk_id=clerk_id,
            email=payload.get("email") or f"{clerk_id}@placeholder.com",
            full_name=payload.get("name") or "New User",
            role="recruiter",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"status": "success", "user_id": user.id, "role": user.role}


# ── Jobs ──────────────────────────────────────────────
@app.post("/api/jobs", response_model=schemas.JobOut)
def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    db_job = models.Job(
        title=job.title,
        description=job.description,
        company=job.company,
        location=job.location,
        job_type=job.job_type,
        experience_level=job.experience_level,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        skills_required=job.skills_required,
        recruiter_id=current_user.id,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@app.get("/api/jobs", response_model=List[schemas.JobOut])
def list_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Job)
    if search:
        query = query.filter(models.Job.title.ilike(f"%{search}%"))
    if location:
        query = query.filter(models.Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(models.Job.job_type == job_type)
    return query.offset(skip).limit(limit).all()


@app.get("/api/jobs/my", response_model=List[schemas.JobOut])
def list_my_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    """List jobs posted by the current authenticated recruiter."""
    return (
        db.query(models.Job)
        .filter(models.Job.recruiter_id == current_user.id)
        .order_by(models.Job.created_at.desc())
        .all()
    )


@app.get("/api/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/jobs/{job_id}/applicants", response_model=List[schemas.ApplicationOut])
def get_job_applicants(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    return (
        db.query(models.Application)
        .filter(models.Application.job_id == job_id)
        .all()
    )


# ── Applications ──────────────────────────────────────
@app.post("/api/applications", response_model=schemas.ApplicationOut)
def create_application(
    app_data: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    # Check for duplicate application
    existing = (
        db.query(models.Application)
        .filter(
            models.Application.candidate_id == current_user.id,
            models.Application.job_id == app_data.job_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="You have already applied to this job."
        )

    db_app = models.Application(
        candidate_id=current_user.id,
        job_id=app_data.job_id,
        notice_period=app_data.notice_period,
        current_ctc=app_data.current_ctc,
        latest_company=app_data.latest_company,
        cover_letter=app_data.cover_letter,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


@app.get("/api/applications", response_model=List[schemas.ApplicationOut])
def list_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    query = db.query(models.Application)
    if status:
        query = query.filter(models.Application.status == status)
    return query.all()


@app.patch("/api/applications/{app_id}/status", response_model=schemas.ApplicationOut)
def update_application_status(
    app_id: int,
    update: schemas.ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    db_app = (
        db.query(models.Application)
        .filter(models.Application.id == app_id)
        .first()
    )
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    db_app.status = update.status.value
    db.commit()
    db.refresh(db_app)
    return db_app


# ── Assessments ───────────────────────────────────────
@app.post("/api/assessments", response_model=schemas.AssessmentOut)
def create_assessment(
    assessment: schemas.AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    # Mock AI-generated questions
    mock_questions = [
        {
            "id": i + 1,
            "question": f"Sample question {i + 1} for {assessment.name}",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0,
        }
        for i in range(assessment.num_questions)
    ]

    db_assessment = models.Assessment(
        job_id=assessment.job_id,
        name=assessment.name,
        assessment_type=assessment.assessment_type,
        num_questions=assessment.num_questions,
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        prompt_used=assessment.prompt_used,
        questions_json=mock_questions,
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


@app.get("/api/assessments/{assessment_id}", response_model=schemas.AssessmentOut)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    assessment = (
        db.query(models.Assessment)
        .filter(models.Assessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


# ── Interviews ────────────────────────────────────────
@app.post("/api/interviews", response_model=schemas.InterviewOut)
def create_interview(
    interview: schemas.InterviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    db_interview = models.Interview(
        application_id=interview.application_id,
        scheduled_at=interview.scheduled_at,
        duration_minutes=interview.duration_minutes,
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview


@app.get("/api/interviews/{interview_id}", response_model=schemas.InterviewOut)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    interview = (
        db.query(models.Interview)
        .filter(models.Interview.id == interview_id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


# ── Company ───────────────────────────────────────────
@app.get("/api/company", response_model=schemas.CompanyOut)
def get_my_company(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    company = (
        db.query(models.Company)
        .filter(models.Company.owner_id == current_user.id)
        .first()
    )
    if not company:
        # Auto-create a default company for the user
        company = models.Company(
            name=current_user.company_name or "My Company",
            owner_id=current_user.id,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


@app.put("/api/company", response_model=schemas.CompanyOut)
def update_my_company(
    update: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    company = (
        db.query(models.Company)
        .filter(models.Company.owner_id == current_user.id)
        .first()
    )
    if not company:
        company = models.Company(
            name=update.name or current_user.company_name or "My Company",
            owner_id=current_user.id,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


# ── Dashboard ─────────────────────────────────────────
@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    jobs_posted = (
        db.query(models.Job)
        .filter(models.Job.recruiter_id == current_user.id)
        .count()
    )

    # Get all job IDs posted by this recruiter
    job_ids_query = db.query(models.Job.id).filter(
        models.Job.recruiter_id == current_user.id
    )

    total_apps = (
        db.query(models.Application)
        .filter(models.Application.job_id.in_(job_ids_query))
        .count()
    )
    shortlisted = (
        db.query(models.Application)
        .filter(
            models.Application.job_id.in_(job_ids_query),
            models.Application.status == "Shortlisted",
        )
        .count()
    )
    rejected = (
        db.query(models.Application)
        .filter(
            models.Application.job_id.in_(job_ids_query),
            models.Application.status == "Rejected",
        )
        .count()
    )
    recent_jobs = (
        db.query(models.Job)
        .filter(models.Job.recruiter_id == current_user.id)
        .order_by(models.Job.created_at.desc())
        .limit(5)
        .all()
    )

    return schemas.DashboardStats(
        jobs_posted=jobs_posted,
        total_applications=total_apps,
        shortlisted=shortlisted,
        rejected=rejected,
        recent_jobs=recent_jobs,
    )
