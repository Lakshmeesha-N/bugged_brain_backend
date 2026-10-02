# Resume Platform Backend

A modular FastAPI backend service for an AI-powered resume, ATS optimization, profile, and job matching platform.

## 📁 Project Structure

```text
resume-platform-backend/
├── src/
│   ├── main.py            # App entrypoint + router aggregation
│   ├── core/              # Config, database, security
│   ├── routers/           # Thin API endpoints
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── resume.py
│   │   ├── ats.py
│   │   ├── jobs.py
│   │   └── admin.py
│   ├── services/          # Business logic
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic validation schemas
│   ├── agents/            # AI Agent implementations (profile, resume, ats)
│   ├── prompts/           # LLM Prompt templates
│   └── utils/             # Helper utilities (e.g., PDF parsing)
├── tests/                 # Unit & integration tests
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables
├── .gitignore             # Git ignore rules
└── README.md
```

## 🚀 Getting Started

### 1. Setup Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and fill in required secrets / API keys:

```bash
cp .env .env.local
```

### 3. Run Development Server

```bash
uvicorn src.main:app --reload
```
