"""
Shared test fixtures for the Hire.ai backend test suite.

Uses an in-memory SQLite database so tests never touch the production
PostgreSQL instance.  Auth is mocked via dependency overrides so every
endpoint can be tested without a running Clerk instance.
"""

import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
import models

# ── In-memory SQLite engine ──────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)

# SQLite doesn't enforce FK constraints by default – turn them on
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


# ── Fixtures ─────────────────────────────────────────────
@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Yield a fresh DB session that rolls back after the test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """
    FastAPI TestClient that uses the test DB session and bypasses Clerk auth.
    The ``require_auth`` dependency is overridden to return a default recruiter
    user that is created automatically.
    """
    from auth import require_auth, get_current_user

    # seed a recruiter so the override has something to return
    recruiter = models.User(
        clerk_id="test_clerk_id",
        email="recruiter@test.com",
        full_name="Test Recruiter",
        role="recruiter",
        company_name="Test Corp",
    )
    db_session.add(recruiter)
    db_session.commit()
    db_session.refresh(recruiter)

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # session closed by db_session fixture

    def _override_require_auth():
        return recruiter

    def _override_get_current_user():
        return recruiter

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_auth] = _override_require_auth
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def recruiter_user(db_session):
    """A recruiter user persisted in the test DB."""
    user = models.User(
        clerk_id="recruiter_clerk_1",
        email="recruiter1@test.com",
        full_name="Recruiter One",
        role="recruiter",
        company_name="Test Corp",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def candidate_user(db_session):
    """A candidate user persisted in the test DB."""
    user = models.User(
        clerk_id="candidate_clerk_1",
        email="candidate1@test.com",
        full_name="Candidate One",
        role="candidate",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def sample_job(db_session, recruiter_user):
    """A job posting owned by ``recruiter_user``."""
    job = models.Job(
        title="Backend Engineer",
        description="Build APIs with FastAPI.",
        company="Test Corp",
        location="Remote",
        job_type="Full Time",
        experience_level="1-3",
        salary_min=15.0,
        salary_max=25.0,
        skills_required=["Python", "FastAPI"],
        recruiter_id=recruiter_user.id,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture()
def sample_application(db_session, candidate_user, sample_job):
    """An application from ``candidate_user`` to ``sample_job``."""
    application = models.Application(
        candidate_id=candidate_user.id,
        job_id=sample_job.id,
        status="Applied",
        notice_period="1 Month",
        current_ctc="10 LPA",
        latest_company="Old Corp",
        cover_letter="I am interested.",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application
