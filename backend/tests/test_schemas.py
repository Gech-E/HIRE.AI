"""
Tests for Pydantic schemas.

Validates field validation, defaults, enum handling, and
the ``from_attributes`` (ORM mode) configuration.
"""

import datetime
import pytest
from pydantic import ValidationError

import schemas


# ── Enum Tests ───────────────────────────────────────────
class TestEnums:
    def test_application_status_values(self):
        assert schemas.ApplicationStatus.Applied.value == "Applied"
        assert schemas.ApplicationStatus.Shortlisted.value == "Shortlisted"
        assert schemas.ApplicationStatus.Rejected.value == "Rejected"
        assert schemas.ApplicationStatus.Scheduled.value == "Scheduled"
        assert schemas.ApplicationStatus.Interviewed.value == "Interviewed"

    def test_job_status_values(self):
        assert schemas.JobStatus.Active.value == "Active"
        assert schemas.JobStatus.Closed.value == "Closed"
        assert schemas.JobStatus.Draft.value == "Draft"

    def test_invalid_application_status(self):
        with pytest.raises(ValueError):
            schemas.ApplicationStatus("InvalidStatus")

    def test_invalid_job_status(self):
        with pytest.raises(ValueError):
            schemas.JobStatus("InvalidStatus")


# ── User Schemas ─────────────────────────────────────────
class TestUserSchemas:
    def test_user_base_required_fields(self):
        user = schemas.UserBase(
            email="a@b.com", full_name="Test", role="recruiter"
        )
        assert user.email == "a@b.com"

    def test_user_base_missing_fields(self):
        with pytest.raises(ValidationError):
            schemas.UserBase(email="a@b.com")  # missing full_name, role

    def test_user_create_optional_fields(self):
        user = schemas.UserCreate(
            email="a@b.com", full_name="Test", role="candidate"
        )
        assert user.clerk_id is None
        assert user.phone is None
        assert user.company_name is None

    def test_user_out_from_attributes(self):
        """UserOut should accept ORM-like dicts with `from_attributes`."""
        data = {
            "id": 1,
            "email": "a@b.com",
            "full_name": "Test",
            "role": "recruiter",
            "avatar_url": None,
            "company_name": None,
            "created_at": datetime.datetime(2026, 1, 1),
        }
        user = schemas.UserOut(**data)
        assert user.id == 1


# ── Job Schemas ──────────────────────────────────────────
class TestJobSchemas:
    def test_job_create_defaults(self):
        job = schemas.JobCreate(
            title="Dev", description="Desc", company="Corp"
        )
        assert job.job_type == "Full Time"
        assert job.skills_required is None

    def test_job_create_all_fields(self):
        job = schemas.JobCreate(
            title="Dev",
            description="Desc",
            company="Corp",
            location="NYC",
            job_type="Contract",
            experience_level="3-5",
            salary_min=50.0,
            salary_max=100.0,
            skills_required=["Python", "Go"],
        )
        assert job.salary_max == 100.0
        assert len(job.skills_required) == 2

    def test_job_create_missing_required(self):
        with pytest.raises(ValidationError):
            schemas.JobCreate(title="Dev")  # missing description, company

    def test_job_out_schema(self):
        data = {
            "id": 1,
            "title": "Dev",
            "description": "D",
            "company": "C",
            "location": "X",
            "job_type": "Full Time",
            "status": "Active",
            "is_open": True,
            "created_at": datetime.datetime(2026, 1, 1),
            "recruiter_id": 1,
        }
        job = schemas.JobOut(**data)
        assert job.applicant_count == 0  # default


# ── Application Schemas ──────────────────────────────────
class TestApplicationSchemas:
    def test_application_create_minimal(self):
        app = schemas.ApplicationCreate(job_id=1)
        assert app.job_id == 1
        assert app.cover_letter is None

    def test_application_create_full(self):
        app = schemas.ApplicationCreate(
            job_id=1,
            notice_period="2 Months",
            current_ctc="12 LPA",
            latest_company="Google",
            cover_letter="Hire me!",
        )
        assert app.latest_company == "Google"

    def test_application_status_update_valid(self):
        update = schemas.ApplicationStatusUpdate(
            status=schemas.ApplicationStatus.Shortlisted
        )
        assert update.status == schemas.ApplicationStatus.Shortlisted

    def test_application_status_update_invalid(self):
        with pytest.raises(ValidationError):
            schemas.ApplicationStatusUpdate(status="Banana")

    def test_application_out_schema(self):
        data = {
            "id": 1,
            "job_id": 1,
            "candidate_id": 2,
            "status": "Applied",
            "applied_at": datetime.datetime(2026, 1, 1),
        }
        out = schemas.ApplicationOut(**data)
        assert out.ai_score is None


# ── Assessment Schemas ───────────────────────────────────
class TestAssessmentSchemas:
    def test_assessment_create_defaults(self):
        a = schemas.AssessmentCreate(
            job_id=1, name="Quiz", assessment_type="MCQ"
        )
        assert a.num_questions == 10
        assert a.duration_minutes == 30
        assert a.due_date is None

    def test_assessment_create_custom(self):
        a = schemas.AssessmentCreate(
            job_id=1,
            name="Hard Quiz",
            assessment_type="Coding",
            num_questions=20,
            duration_minutes=60,
        )
        assert a.num_questions == 20

    def test_assessment_out(self):
        data = {
            "id": 1,
            "job_id": 1,
            "name": "Quiz",
            "assessment_type": "MCQ",
            "num_questions": 10,
            "duration_minutes": 30,
            "created_at": datetime.datetime(2026, 1, 1),
        }
        out = schemas.AssessmentOut(**data)
        assert out.questions_json is None


# ── Interview Schemas ────────────────────────────────────
class TestInterviewSchemas:
    def test_interview_create_defaults(self):
        i = schemas.InterviewCreate(application_id=1)
        assert i.duration_minutes == 30
        assert i.scheduled_at is None

    def test_interview_out(self):
        data = {
            "id": 1,
            "application_id": 1,
            "duration_minutes": 30,
            "status": "Pending",
            "created_at": datetime.datetime(2026, 1, 1),
        }
        out = schemas.InterviewOut(**data)
        assert out.score is None
        assert out.ai_notes is None


# ── Company Schemas ──────────────────────────────────────
class TestCompanySchemas:
    def test_company_update_partial(self):
        update = schemas.CompanyUpdate(name="New Name")
        dumped = update.model_dump(exclude_unset=True)
        assert "name" in dumped
        assert "industry" not in dumped

    def test_company_out(self):
        data = {
            "id": 1,
            "name": "Corp",
            "created_at": datetime.datetime(2026, 1, 1),
        }
        out = schemas.CompanyOut(**data)
        assert out.logo_url is None


# ── Dashboard Stats ──────────────────────────────────────
class TestDashboardStats:
    def test_dashboard_stats(self):
        stats = schemas.DashboardStats(
            jobs_posted=5,
            total_applications=20,
            shortlisted=8,
            rejected=3,
            recent_jobs=[],
        )
        assert stats.jobs_posted == 5
        assert stats.recent_jobs == []
