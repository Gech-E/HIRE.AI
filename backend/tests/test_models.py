"""
Tests for SQLAlchemy ORM models.

Validates table creation, column constraints, default values,
and inter-model relationships.
"""

import datetime
import pytest
from sqlalchemy.exc import IntegrityError

import models


# ── User Model ───────────────────────────────────────────
class TestUserModel:
    def test_create_user(self, db_session):
        user = models.User(
            clerk_id="clerk_111",
            email="test@example.com",
            full_name="Test User",
            role="recruiter",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "recruiter"
        assert user.created_at is not None

    def test_user_email_unique(self, db_session):
        """Two users cannot share the same email."""
        u1 = models.User(email="dup@test.com", full_name="A", role="recruiter")
        u2 = models.User(email="dup@test.com", full_name="B", role="candidate")
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_clerk_id_unique(self, db_session):
        """Two users cannot share the same clerk_id."""
        u1 = models.User(
            clerk_id="same", email="a@t.com", full_name="A", role="recruiter"
        )
        u2 = models.User(
            clerk_id="same", email="b@t.com", full_name="B", role="candidate"
        )
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_nullable_fields(self, db_session):
        """Optional fields like phone, avatar_url, company_name can be None."""
        user = models.User(
            email="min@test.com", full_name="Min", role="candidate"
        )
        db_session.add(user)
        db_session.commit()

        assert user.phone is None
        assert user.avatar_url is None
        assert user.company_name is None
        assert user.clerk_id is None


# ── Job Model ────────────────────────────────────────────
class TestJobModel:
    def test_create_job(self, db_session, recruiter_user):
        job = models.Job(
            title="Data Scientist",
            description="ML role",
            company="AI Corp",
            recruiter_id=recruiter_user.id,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.id is not None
        assert job.title == "Data Scientist"
        assert job.status == "Active"
        assert job.is_open is True
        assert job.job_type == "Full Time"

    def test_job_defaults(self, db_session, recruiter_user):
        """Verify column defaults: status='Active', is_open=True, job_type='Full Time'."""
        job = models.Job(
            title="Test",
            description="Desc",
            company="C",
            recruiter_id=recruiter_user.id,
        )
        db_session.add(job)
        db_session.commit()

        assert job.status == "Active"
        assert job.is_open is True
        assert job.job_type == "Full Time"

    def test_job_recruiter_relationship(self, db_session, recruiter_user):
        job = models.Job(
            title="Rel Test",
            description="D",
            company="C",
            recruiter_id=recruiter_user.id,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.recruiter.id == recruiter_user.id
        assert job in recruiter_user.jobs

    def test_job_json_skills(self, db_session, recruiter_user):
        """skills_required stores a JSON list correctly."""
        skills = ["Python", "SQL", "Docker"]
        job = models.Job(
            title="DevOps",
            description="Infra",
            company="C",
            skills_required=skills,
            recruiter_id=recruiter_user.id,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.skills_required == skills


# ── Application Model ────────────────────────────────────
class TestApplicationModel:
    def test_create_application(self, db_session, sample_application):
        assert sample_application.id is not None
        assert sample_application.status == "Applied"
        assert sample_application.applied_at is not None

    def test_application_relationships(
        self, db_session, sample_application, candidate_user, sample_job
    ):
        assert sample_application.candidate.id == candidate_user.id
        assert sample_application.job.id == sample_job.id
        assert sample_application in sample_job.applications

    def test_application_defaults(self, db_session, candidate_user, sample_job):
        app = models.Application(
            candidate_id=candidate_user.id,
            job_id=sample_job.id,
        )
        db_session.add(app)
        db_session.commit()

        assert app.status == "Applied"
        assert app.ai_score is None
        assert app.resume_url is None


# ── Assessment Model ─────────────────────────────────────
class TestAssessmentModel:
    def test_create_assessment(self, db_session, sample_job):
        assessment = models.Assessment(
            job_id=sample_job.id,
            name="Python Quiz",
            assessment_type="MCQ",
            num_questions=5,
            duration_minutes=15,
            questions_json=[{"q": "What is Python?", "a": "Language"}],
        )
        db_session.add(assessment)
        db_session.commit()
        db_session.refresh(assessment)

        assert assessment.id is not None
        assert assessment.num_questions == 5
        assert assessment.questions_json[0]["q"] == "What is Python?"

    def test_assessment_defaults(self, db_session, sample_job):
        assessment = models.Assessment(
            job_id=sample_job.id,
            name="Default Test",
            assessment_type="Coding",
        )
        db_session.add(assessment)
        db_session.commit()

        assert assessment.num_questions == 10
        assert assessment.duration_minutes == 30

    def test_assessment_job_relationship(self, db_session, sample_job):
        a = models.Assessment(
            job_id=sample_job.id, name="T", assessment_type="MCQ"
        )
        db_session.add(a)
        db_session.commit()
        db_session.refresh(a)

        assert a.job.id == sample_job.id
        assert a in sample_job.assessments


# ── Interview Model ──────────────────────────────────────
class TestInterviewModel:
    def test_create_interview(self, db_session, sample_application):
        interview = models.Interview(
            application_id=sample_application.id,
            duration_minutes=45,
            status="Scheduled",
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)

        assert interview.id is not None
        assert interview.status == "Scheduled"
        assert interview.duration_minutes == 45

    def test_interview_defaults(self, db_session, sample_application):
        interview = models.Interview(
            application_id=sample_application.id,
        )
        db_session.add(interview)
        db_session.commit()

        assert interview.status == "Pending"
        assert interview.duration_minutes == 30
        assert interview.score is None

    def test_interview_application_relationship(
        self, db_session, sample_application
    ):
        interview = models.Interview(
            application_id=sample_application.id,
        )
        db_session.add(interview)
        db_session.commit()
        db_session.refresh(interview)

        assert interview.application.id == sample_application.id
        assert interview in sample_application.interviews


# ── Company Model ────────────────────────────────────────
class TestCompanyModel:
    def test_create_company(self, db_session, recruiter_user):
        company = models.Company(
            name="Acme Inc",
            industry="Tech",
            owner_id=recruiter_user.id,
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)

        assert company.id is not None
        assert company.name == "Acme Inc"
        assert company.owner.id == recruiter_user.id

    def test_company_nullable_fields(self, db_session, recruiter_user):
        company = models.Company(
            name="Min Co", owner_id=recruiter_user.id
        )
        db_session.add(company)
        db_session.commit()

        assert company.logo_url is None
        assert company.description is None
        assert company.website is None
        assert company.industry is None
