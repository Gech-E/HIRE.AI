from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String)  # "recruiter" or "candidate"
    company_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="recruiter")
    applications = relationship("Application", back_populates="candidate")
    company = relationship("Company", back_populates="owner", uselist=False)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    logo_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="company")
    jobs = relationship("Job", back_populates="company_ref")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    company = Column(String)
    location = Column(String, nullable=True)
    job_type = Column(String, default="Full Time")  # Full Time, Part Time, Contract, Internship
    experience_level = Column(String, nullable=True)  # 0-1, 1-3, 3-5, 5+
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    skills_required = Column(JSON, nullable=True)  # List of skills
    status = Column(String, default="Active")  # Active, Closed, Draft
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    recruiter = relationship("User", back_populates="jobs")
    company_ref = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    assessments = relationship("Assessment", back_populates="job")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String, default="Applied")  # Applied, Shortlisted, Rejected, Scheduled, Interviewed
    notice_period = Column(String, nullable=True)
    current_ctc = Column(String, nullable=True)
    latest_company = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    cover_letter = Column(Text, nullable=True)
    ai_score = Column(Float, nullable=True)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interviews = relationship("Interview", back_populates="application")


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    name = Column(String)
    assessment_type = Column(String)  # MCQ, Coding, Written
    num_questions = Column(Integer, default=10)
    duration_minutes = Column(Integer, default=30)
    due_date = Column(DateTime, nullable=True)
    questions_json = Column(JSON, nullable=True)
    prompt_used = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="assessments")


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    scheduled_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="Pending")  # Pending, Scheduled, Completed, Cancelled
    transcript_json = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    ai_notes = Column(Text, nullable=True)
    recording_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("Application", back_populates="interviews")
