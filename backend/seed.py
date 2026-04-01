import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database import Base, DATABASE_URL
import models
import datetime

load_dotenv()

# We might need to unquote the URL if it has a % in it, similar to what we did in alembic/env.py
from urllib.parse import unquote
import psycopg2

def seed_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create dummy users
    recruiter = db.query(models.User).filter_by(email="nikhil@arcitech.com").first()
    if not recruiter:
        recruiter = models.User(
            email="nikhil@arcitech.com",
            full_name="Nikhil J",
            role="recruiter",
            company_name="Arcitech"
        )
        db.add(recruiter)
    
    candidate = db.query(models.User).filter_by(email="candidate@example.com").first()
    if not candidate:
        candidate = models.User(
            email="candidate@example.com",
            full_name="Srushti H",
            role="candidate"
        )
        db.add(candidate)
    
    db.commit()

    # Create dummy jobs
    if db.query(models.Job).count() == 0:
        jobs = [
            models.Job(
                title="UI/UX Designer",
                company="Arcitech",
                description="At Arcitech, we are seeking a talented and experienced UI/UX Design professional to join our team. As a leading design company, we are looking for someone who can create intuitive, user-centered designs that deliver exceptional digital experiences.",
                location="Lower Parel, Mumbai",
                job_type="Full Time",
                experience_level="0-1 Experience",
                salary_min=10.0,
                salary_max=12.0,
                status="Active",
                skills_required=["Figma", "Adobe XD", "UI Design", "Prototyping", "User Research"],
                recruiter_id=recruiter.id
            ),
            models.Job(
                title="Frontend Developer",
                company="Arcitech",
                description="We are looking for a skilled Frontend Developer proficient in React.js and TypeScript to build responsive, high-performance web applications.",
                location="Bangalore, India",
                job_type="Full Time",
                experience_level="1-3 Experience",
                salary_min=12.0,
                salary_max=18.0,
                status="Active",
                skills_required=["React", "TypeScript", "Next.js", "CSS", "REST APIs"],
                recruiter_id=recruiter.id
            ),
            models.Job(
                title="Backend Engineer",
                company="Arcitech",
                description="Join our backend team to design and build scalable APIs and microservices using Python and FastAPI.",
                location="Remote",
                job_type="Full Time",
                experience_level="3-5 Experience",
                salary_min=20.0,
                salary_max=30.0,
                status="Active",
                skills_required=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                recruiter_id=recruiter.id
            ),
        ]
        db.add_all(jobs)
        db.commit()

    # Create dummy applications
    if db.query(models.Application).count() == 0:
        job = db.query(models.Job).first()
        apps = [
            models.Application(
                candidate_id=candidate.id,
                job_id=job.id,
                status="Shortlisted",
                notice_period="Immediately",
                current_ctc="5 LPA",
                latest_company="Arcitech"
            ),
            models.Application(
                candidate_id=candidate.id,
                job_id=job.id,
                status="Rejected",
                notice_period="1 Months",
                current_ctc="4 LPA",
                latest_company="TCS"
            ),
        ]
        db.add_all(apps)
        db.commit()

    print("Database seeded with sample data.")
    db.close()

if __name__ == "__main__":
    seed_db()
