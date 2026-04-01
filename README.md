<div align="center">
  
# 🎯 Hire.ai
**The AI-Powered Full-Stack Recruitment Platform**

[![Top Langs](https://img.shields.io/badge/Language-TypeScript%20%7C%20Python-blue.svg)](#)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js-black?logo=next.js)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](#)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql)](#)
[![Auth](https://img.shields.io/badge/Authentication-Clerk-6C47FF?logo=clerk&logoColor=white)](#)

*Hire.ai seamlessly bridges the gap between top talent and leading companies through intelligent AI-driven screening, role-based workflows, and a hyper-modern responsive interface.*

[Features](#-features) • [Tech Stack](#-tech-stack) • [Getting Started](#-getting-started) • [Architecture](#-architecture) • [Testing](#%EF%B8%8F-testing)

</div>

---

## ✨ Features

- **🎭 Multi-Persona Role Access (RBAC):** Intuitive onboarding flow with dedicated workspaces for **Job Seekers** out looking for their dream role, and **Recruiters** who are hiring top talent. 
- **🤖 AI-Driven Assessments & Interviews:** Automated generation of technical screening tests tailored to job descriptions, including dynamic live mock interviews powered by advanced AI mapping. 
- **💼 Recruiter Dashboard:** Powerful insights board to track active job listings, review applicant status pipelines (Shortlisted, Interviewed, Rejected), and manage company profiles.
- **🔍 Intelligent Job Feed:** Fully reactive and searchable job feed for candidates, featuring custom location tagging and role-fit analysis.
- **🔐 Secure Authentication:** Enterprise-grade security powered by Clerk, ensuring that tokens, candidate resumes, and recruiter resources are structurally guarded.

---

## 🛠 Tech Stack

Hire.ai is built using modern, bleeding-edge web technologies designed for absolute vertical scalability. 

**Frontend:**
- **Framework:** Next.js (React 18)
- **Styling:** Tailwind CSS + Custom CSS Variables for Glassmorphism & UI themes
- **Icons:** Lucide React
- **Auth Interface:** Clerk (`@clerk/nextjs`)

**Backend:**
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy + Alembic (Migrations)
- **Validation:** Pydantic
- **Testing Engine:** Pytest & HTTPX

---

## 🚀 Getting Started

Follow these steps to get a local development environment running.

### 1. Requirements
- Node.js (v18+)
- Python (3.10+) 
- A running PostgreSQL instance
- A [Clerk.com](https://clerk.com/) account for authentication keys. 

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/hire.ai.git
cd hire.ai
```

### 3. Backend Setup
The backend runs on FastAPI and interfaces with PostgreSQL.
```bash
# Navigate to the backend directory
cd backend

# Create and activate a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file locally with the following keys:
# DATABASE_URL=postgresql://user:password@localhost:5432/hire_db
# CLERK_SECRET_KEY=your_clerk_secret_key
# OPENAI_API_KEY=your_openai_key

# Run the backend development server
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000/docs`.

### 4. Frontend Setup
The frontend runs on Next.js.
```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Create a .env.local file locally with the following keys:
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
# CLERK_SECRET_KEY=your_clerk_secret_key
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Run the development server
npm run dev
```
Access the web app at `http://localhost:3000`.

---

## 🛡️ Testing

The backend maintains a heavily guarded test suite encompassing data models, ORM schemas, CRUD endpoints, and mocked Role-Based Access controls using a transient SQLite database instance to ensure your production data is never touched.

To run the full backend testing suite:
```bash
cd backend
python -m pytest tests/ -v
```

---

<div align="center">
  <i>Built with ❤️ precisely for the future of Intelligent Recruitment.</i>
</div>
