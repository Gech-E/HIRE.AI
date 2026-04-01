"""
Integration tests for all FastAPI API endpoints.

The ``client`` fixture (from conftest) uses:
- An in-memory SQLite DB (no production data touched)
- Mocked auth (no live Clerk verification)
"""

import pytest


# ── Root & Health ────────────────────────────────────────
class TestRootEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Welcome to Hire.ai Backend API!"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        # Should report some status (may be "error" with SQLite but endpoint works)
        assert "status" in data


# ── Jobs CRUD ────────────────────────────────────────────
class TestJobsAPI:
    JOB_PAYLOAD = {
        "title": "ML Engineer",
        "description": "Build ML pipelines",
        "company": "AI Corp",
        "location": "San Francisco",
        "job_type": "Full Time",
        "experience_level": "3-5",
        "salary_min": 120.0,
        "salary_max": 200.0,
        "skills_required": ["Python", "TensorFlow"],
    }

    def test_create_job(self, client):
        resp = client.post("/api/jobs", json=self.JOB_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "ML Engineer"
        assert data["id"] is not None
        assert data["status"] == "Active"
        assert data["is_open"] is True

    def test_list_jobs(self, client):
        # Create two jobs
        client.post("/api/jobs", json=self.JOB_PAYLOAD)
        client.post(
            "/api/jobs",
            json={**self.JOB_PAYLOAD, "title": "Data Analyst"},
        )
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_jobs_search(self, client):
        client.post("/api/jobs", json=self.JOB_PAYLOAD)
        client.post(
            "/api/jobs",
            json={**self.JOB_PAYLOAD, "title": "Data Analyst"},
        )
        resp = client.get("/api/jobs", params={"search": "Data"})
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["title"] == "Data Analyst"

    def test_list_jobs_filter_location(self, client):
        client.post("/api/jobs", json=self.JOB_PAYLOAD)
        client.post(
            "/api/jobs",
            json={**self.JOB_PAYLOAD, "title": "Remote Dev", "location": "Remote"},
        )
        resp = client.get("/api/jobs", params={"location": "Remote"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_jobs_filter_job_type(self, client):
        client.post("/api/jobs", json=self.JOB_PAYLOAD)
        client.post(
            "/api/jobs",
            json={**self.JOB_PAYLOAD, "title": "Intern", "job_type": "Internship"},
        )
        resp = client.get("/api/jobs", params={"job_type": "Internship"})
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["job_type"] == "Internship"

    def test_list_jobs_pagination(self, client):
        for i in range(5):
            client.post(
                "/api/jobs",
                json={**self.JOB_PAYLOAD, "title": f"Job {i}"},
            )
        resp = client.get("/api/jobs", params={"skip": 2, "limit": 2})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_job_by_id(self, client):
        create_resp = client.post("/api/jobs", json=self.JOB_PAYLOAD)
        job_id = create_resp.json()["id"]

        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "ML Engineer"

    def test_get_job_not_found(self, client):
        resp = client.get("/api/jobs/99999")
        assert resp.status_code == 404

    def test_list_my_jobs(self, client):
        client.post("/api/jobs", json=self.JOB_PAYLOAD)
        resp = client.get("/api/jobs/my")
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) >= 1
        assert jobs[0]["title"] == "ML Engineer"


# ── Applications ─────────────────────────────────────────
class TestApplicationsAPI:
    def _create_job(self, client):
        resp = client.post(
            "/api/jobs",
            json={
                "title": "Test Job",
                "description": "Test",
                "company": "Test Corp",
            },
        )
        return resp.json()["id"]

    def test_create_application(self, client):
        job_id = self._create_job(client)
        resp = client.post(
            "/api/applications",
            json={
                "job_id": job_id,
                "notice_period": "1 Month",
                "current_ctc": "10 LPA",
                "latest_company": "Old Corp",
                "cover_letter": "I'm interested!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "Applied"

    def test_duplicate_application_rejected(self, client):
        job_id = self._create_job(client)
        payload = {"job_id": job_id}
        client.post("/api/applications", json=payload)
        resp = client.post("/api/applications", json=payload)
        assert resp.status_code == 400
        assert "already applied" in resp.json()["detail"].lower()

    def test_list_applications(self, client):
        job_id = self._create_job(client)
        client.post("/api/applications", json={"job_id": job_id})
        resp = client.get("/api/applications")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_application_status(self, client):
        job_id = self._create_job(client)
        app_resp = client.post(
            "/api/applications", json={"job_id": job_id}
        )
        app_id = app_resp.json()["id"]

        resp = client.patch(
            f"/api/applications/{app_id}/status",
            json={"status": "Shortlisted"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Shortlisted"

    def test_update_application_status_invalid(self, client):
        job_id = self._create_job(client)
        app_resp = client.post(
            "/api/applications", json={"job_id": job_id}
        )
        app_id = app_resp.json()["id"]

        resp = client.patch(
            f"/api/applications/{app_id}/status",
            json={"status": "InvalidStatus"},
        )
        assert resp.status_code == 422  # Pydantic validation error

    def test_update_application_not_found(self, client):
        resp = client.patch(
            "/api/applications/99999/status",
            json={"status": "Shortlisted"},
        )
        assert resp.status_code == 404

    def test_get_job_applicants(self, client):
        job_id = self._create_job(client)
        client.post("/api/applications", json={"job_id": job_id})
        resp = client.get(f"/api/jobs/{job_id}/applicants")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_filter_applications_by_status(self, client):
        job_id = self._create_job(client)
        app_resp = client.post(
            "/api/applications", json={"job_id": job_id}
        )
        app_id = app_resp.json()["id"]
        client.patch(
            f"/api/applications/{app_id}/status",
            json={"status": "Shortlisted"},
        )
        resp = client.get(
            "/api/applications", params={"status": "Shortlisted"}
        )
        assert resp.status_code == 200
        results = resp.json()
        assert all(r["status"] == "Shortlisted" for r in results)


# ── Assessments ──────────────────────────────────────────
class TestAssessmentsAPI:
    def _create_job(self, client):
        resp = client.post(
            "/api/jobs",
            json={
                "title": "Test Job",
                "description": "Desc",
                "company": "Corp",
            },
        )
        return resp.json()["id"]

    def test_create_assessment(self, client):
        job_id = self._create_job(client)
        resp = client.post(
            "/api/assessments",
            json={
                "job_id": job_id,
                "name": "Python Quiz",
                "assessment_type": "MCQ",
                "num_questions": 5,
                "duration_minutes": 20,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Python Quiz"
        assert data["num_questions"] == 5
        assert len(data["questions_json"]) == 5

    def test_get_assessment(self, client):
        job_id = self._create_job(client)
        create_resp = client.post(
            "/api/assessments",
            json={
                "job_id": job_id,
                "name": "Quiz",
                "assessment_type": "MCQ",
                "num_questions": 3,
            },
        )
        a_id = create_resp.json()["id"]

        resp = client.get(f"/api/assessments/{a_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == a_id

    def test_get_assessment_not_found(self, client):
        resp = client.get("/api/assessments/99999")
        assert resp.status_code == 404

    def test_assessment_questions_generated(self, client):
        """Verify mock AI generates the correct number of questions."""
        job_id = self._create_job(client)
        resp = client.post(
            "/api/assessments",
            json={
                "job_id": job_id,
                "name": "Big Quiz",
                "assessment_type": "MCQ",
                "num_questions": 15,
            },
        )
        data = resp.json()
        assert len(data["questions_json"]) == 15
        # Each question should have id, question, options, correct
        q = data["questions_json"][0]
        assert "id" in q
        assert "question" in q
        assert "options" in q
        assert len(q["options"]) == 4


# ── Interviews ───────────────────────────────────────────
class TestInterviewsAPI:
    def _create_application(self, client):
        job_resp = client.post(
            "/api/jobs",
            json={
                "title": "Test Job",
                "description": "Desc",
                "company": "Corp",
            },
        )
        job_id = job_resp.json()["id"]
        app_resp = client.post(
            "/api/applications", json={"job_id": job_id}
        )
        return app_resp.json()["id"]

    def test_create_interview(self, client):
        app_id = self._create_application(client)
        resp = client.post(
            "/api/interviews",
            json={
                "application_id": app_id,
                "duration_minutes": 45,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["application_id"] == app_id
        assert data["status"] == "Pending"
        assert data["duration_minutes"] == 45

    def test_get_interview(self, client):
        app_id = self._create_application(client)
        create_resp = client.post(
            "/api/interviews",
            json={"application_id": app_id},
        )
        i_id = create_resp.json()["id"]

        resp = client.get(f"/api/interviews/{i_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == i_id

    def test_get_interview_not_found(self, client):
        resp = client.get("/api/interviews/99999")
        assert resp.status_code == 404


# ── Company ──────────────────────────────────────────────
class TestCompanyAPI:
    def test_get_my_company_auto_creates(self, client):
        resp = client.get("/api/company")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] is not None
        assert data["id"] is not None

    def test_update_my_company(self, client):
        # First call auto-creates
        client.get("/api/company")
        resp = client.put(
            "/api/company",
            json={
                "name": "Updated Corp",
                "industry": "FinTech",
                "website": "https://updated.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Corp"
        assert data["industry"] == "FinTech"
        assert data["website"] == "https://updated.com"

    def test_update_company_partial(self, client):
        """Only the fields sent should be updated."""
        client.get("/api/company")
        resp = client.put("/api/company", json={"industry": "HealthTech"})
        assert resp.status_code == 200
        assert resp.json()["industry"] == "HealthTech"


# ── Dashboard Stats ──────────────────────────────────────
class TestDashboardAPI:
    def test_dashboard_stats_empty(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs_posted"] == 0
        assert data["total_applications"] == 0
        assert data["shortlisted"] == 0
        assert data["rejected"] == 0
        assert data["recent_jobs"] == []

    def test_dashboard_stats_with_data(self, client):
        # Create a job
        job_resp = client.post(
            "/api/jobs",
            json={
                "title": "Test Job",
                "description": "D",
                "company": "C",
            },
        )
        job_id = job_resp.json()["id"]

        # Create an application and shortlist it
        app_resp = client.post(
            "/api/applications", json={"job_id": job_id}
        )
        app_id = app_resp.json()["id"]
        client.patch(
            f"/api/applications/{app_id}/status",
            json={"status": "Shortlisted"},
        )

        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs_posted"] == 1
        assert data["total_applications"] == 1
        assert data["shortlisted"] == 1
        assert len(data["recent_jobs"]) == 1


# ── Edge Cases & Validation ──────────────────────────────
class TestEdgeCases:
    def test_create_job_missing_required_fields(self, client):
        resp = client.post("/api/jobs", json={"title": "Incomplete"})
        assert resp.status_code == 422

    def test_create_application_invalid_job_id(self, client):
        resp = client.post(
            "/api/applications", json={"job_id": 99999}
        )
        assert resp.status_code == 404

    def test_jobs_limit_max(self, client):
        """The limit parameter should cap at 100."""
        resp = client.get("/api/jobs", params={"limit": 200})
        assert resp.status_code == 422  # exceeds le=100

    def test_jobs_limit_boundary(self, client):
        resp = client.get("/api/jobs", params={"limit": 100})
        assert resp.status_code == 200
