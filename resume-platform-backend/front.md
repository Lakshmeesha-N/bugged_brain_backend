# Frontend Integration Guide - Resume Platform Backend

> **Base URL:** `http://localhost:8000` (development). All protected routes require `Authorization: Bearer <firebase_id_token>`

---

## Table of Contents

1. [Authentication Model](#1-authentication-model)
2. [Global Error Shapes](#2-global-error-shapes)
3. [Health](#3-health)
4. [Profile](#4-profile)
5. [Templates](#5-templates)
6. [Resume](#6-resume)
7. [ATS Checker](#7-ats-checker)
8. [Jobs](#8-jobs)
9. [Usage & Plans](#9-usage--plans)
10. [Admin](#10-admin)
11. [Rate Limiting (429)](#11-rate-limiting-429)
12. [Frontend State Machine - Resume Generation](#12-frontend-state-machine---resume-generation)
13. [Frontend State Machine - ATS Check](#13-frontend-state-machine---ats-check)
14. [Recommended UI Pages & Components](#14-recommended-ui-pages--components)

---

## 1. Authentication Model

| Item | Detail |
|---|---|
| Provider | Firebase Auth (Google / Email) |
| Token type | Firebase ID Token (JWT) |
| Header | `Authorization: Bearer <id_token>` |
| Token refresh | Firebase SDK auto-refreshes; always call `currentUser.getIdToken()` before each API call |
| Admin flag | Set via Firebase custom claim `admin: true` - backend reads it from the verified token |

**How to get the token (JavaScript):**
```js
const token = await firebase.auth().currentUser.getIdToken(true);
```

---

## 2. Global Error Shapes

### Standard error (all non-429)
```json
{ "detail": "Human-readable message" }
```

### Rate limit error (429 only)
```json
{
  "detail": {
    "code": "limit_reached",
    "message": "You have used your daily AI limit. Upgrade to premium to continue.",
    "plan": "free",
    "used": 50000,
    "limit": 50000,
    "resets_at": 3600,
    "upgrade_url": "https://stripe.example.com"
  }
}
```

> `upgrade_url` is `null` for premium users. `resets_at` is **seconds until midnight IST**.

### Common HTTP codes

| Code | Meaning |
|---|---|
| `401` | Missing / expired token |
| `403` | Admin route, user is not admin |
| `404` | Resource not found |
| `413` | File > 5 MB |
| `415` | Unsupported file type (not PDF/DOCX) |
| `422` | Validation error or scanned/empty PDF |
| `429` | Daily AI token limit reached |
| `502` | Gemini LLM error |

---

## 3. Health

### `GET /health`
No auth required.
```json
{ "status": "ok" }
```

### `GET /health/db`
```json
{ "db": "connected" }
```

---

## 4. Profile

**Prefix:** `/profile` | **Auth:** required

### `PUT /profile`
Create or update the user's profile.

**Required fields:** `name`, `email`, `education` (non-empty array)

**Request body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "location": "New York, NY",
  "summary": "Full Stack Developer with 3 years of experience.",
  "links": {
    "linkedin": "https://linkedin.com/in/janedoe",
    "github": "https://github.com/janedoe",
    "portfolio": "https://janedoe.dev",
    "other": null
  },
  "skills": ["Python", "FastAPI", "React"],
  "projects": [
    {
      "title": "Resume AI",
      "description": "AI-powered resume platform",
      "tech_stack": ["FastAPI", "React", "Gemini"],
      "link": "https://github.com/janedoe/resume-ai"
    }
  ],
  "experience": [
    {
      "company": "Tech Corp",
      "role": "Software Engineer",
      "duration": "Jan 2022 - Present",
      "description": "Built scalable backend APIs"
    }
  ],
  "education": [
    {
      "institution": "University of Tech",
      "degree": "B.S. Computer Science",
      "year": "2022",
      "grade": "3.9 GPA"
    }
  ],
  "achievements": [
    { "title": "Hackathon Winner", "description": "1st of 50 teams", "year": "2023" }
  ],
  "certifications": [
    { "name": "GCP Cloud Architect", "issuer": "Google", "year": "2024" }
  ],
  "publications": [
    { "title": "Scalable Microservices", "venue": "Tech Journal", "year": "2024", "link": "https://example.com" }
  ],
  "extracurriculars": [
    { "title": "Open Source Club", "role": "Lead", "description": "Organized workshops" }
  ],
  "languages": ["English", "Spanish"]
}
```

**Response `200`:** The saved profile object (same shape as request body).

---

### `GET /profile`
**Response:** `200` profile object, `404` if no profile exists yet.

---

### `DELETE /profile`
**Response:** `200 { "deleted": true }`

---

## 5. Templates

**Prefix:** `/templates` | **Auth:** required

### `GET /templates`
List all available resume templates.

**Response:**
```json
[
  {
    "id": "classic",
    "name": "Classic",
    "preview_url": "https://storage.googleapis.com/.../classic/preview.png",
    "required": ["name", "email", "education"],
    "optional": ["phone", "location", "links", "summary", "skills", "projects", "experience", "achievements", "certifications", "extracurriculars"],
    "limits": { "projects": 3, "bullets_per_item": 3 }
  }
]
```

### `GET /templates/{template_id}`
Single template metadata. `404` if not found.

---

## 6. Resume

**Prefix:** `/resume` | **Auth:** required | **`POST /generate` is rate-limited**

### `POST /resume/generate`

**Request body:**
```json
{
  "template_id": "classic",
  "extra_info": "Emphasize backend work and GCP skills.",
  "answers": []
}
```

`answers` is an array of `{ "question": "...", "answer": "..." }`. Pass the previously returned questions with answers on retry.

**Response - needs more info (`200`):**
```json
{
  "status": "needs_info",
  "questions": [
    "What was your primary role at Tech Corp?",
    "Which projects should be highlighted?"
  ],
  "resume_id": null
}
```

Display the questions to the user, collect answers, then re-POST with `answers` filled in.

**Response - ready (`200`):**
```json
{
  "status": "ready",
  "questions": null,
  "resume_id": "abc123xyz"
}
```

Use `resume_id` to download the PDF.

---

### `GET /resume/{resume_id}/pdf`

**Response:** `200 application/pdf` binary stream
`Content-Disposition: attachment; filename="resume.pdf"`

Open in a new tab or trigger download via blob URL:
```js
const blob = await res.blob();
const url = URL.createObjectURL(blob);
window.open(url);
```

---

### `GET /resume`
List all the user's generated resumes.

**Response:**
```json
[
  {
    "id": "abc123xyz",
    "template_id": "classic",
    "created_at": "2026-10-03T10:00:00Z",
    "content": {}
  }
]
```

### `DELETE /resume/{resume_id}`
**Response:** `200 { "deleted": true }`

---

## 7. ATS Checker

**Prefix:** `/ats` | **Auth:** required | **Rate-limited**

### `POST /ats/check`

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | File | YES | `.pdf` or `.docx` only, max 5 MB |
| `job_title` | string (form) | NO | e.g. `"Software Engineer"` |
| `job_description` | string (form) | NO | Full JD text |

**JavaScript example:**
```js
const form = new FormData();
form.append("file", fileInput.files[0]);
form.append("job_title", "Software Engineer");
form.append("job_description", jdText);

const res = await fetch("/ats/check", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: form,
});
```

**Response `200`:**
```json
{
  "overall_score": 85,
  "label": "Good",
  "role_used": "Software Engineer",
  "summary": "Strong match with the JD. Well-structured resume.",
  "breakdown": [
    { "category": "keywords_match", "score": 25, "max": 30, "comment": "Most keywords present" },
    { "category": "sections_and_structure", "score": 18, "max": 20, "comment": "All key sections present" },
    { "category": "formatting_readability", "score": 14, "max": 15, "comment": "Clean layout" },
    { "category": "impact_and_achievements", "score": 16, "max": 20, "comment": "Good quantification" },
    { "category": "clarity_and_length", "score": 12, "max": 15, "comment": "Appropriate length" }
  ],
  "matched_keywords": ["python", "fastapi", "docker", "gcp"],
  "missing_keywords": ["kubernetes", "terraform"],
  "strengths": ["Strong project descriptions", "Relevant experience"],
  "improvements": [
    {
      "priority": "high",
      "section": "Experience",
      "issue": "Missing quantified metrics",
      "suggestion": "Add numbers like '20% performance improvement'"
    }
  ]
}
```

**Score to Label mapping:**

| Score | Label |
|---|---|
| 90-100 | Excellent |
| 75-89 | Good |
| 60-74 | Fair |
| 0-59 | Poor |

---

## 8. Jobs

**Prefix:** `/jobs` | **Auth:** required

### `GET /jobs`
List published job postings with optional filters.

**Query params:**

| Param | Type | Example |
|---|---|---|
| `category` | string | `"engineering"` |
| `job_type` | string | `"full_time"`, `"internship"`, `"part_time"`, `"contract"`, `"freelance"` |
| `location` | string | `"Remote"` |
| `q` | string | Search title/company |
| `skip` | int | Pagination offset (default 0) |
| `limit` | int | Page size (default 20, max 100) |

**Response:**
```json
[
  {
    "id": "job123",
    "title": "Backend Engineer",
    "company": "Acme Corp",
    "location": "Remote",
    "job_type": "full_time",
    "category": "engineering",
    "description": "We are looking for...",
    "apply_url": "https://acme.com/careers/123",
    "created_at": "2026-10-01T00:00:00Z",
    "is_active": true
  }
]
```

### `GET /jobs/{job_id}`
Single job posting. `404` if not found or inactive.

---

## 9. Usage & Plans

**Prefix:** `/usage` | **Auth:** required

### `GET /usage/me`

**Response:**
```json
{
  "plan": "free",
  "tokens_used": 12500,
  "limit": 50000,
  "remaining": 37500,
  "requests": 3,
  "resets_at": 21600,
  "upgrade_url": "https://stripe.example.com"
}
```

| Field | Notes |
|---|---|
| `plan` | `"free"` or `"premium"` |
| `tokens_used` | Tokens consumed today (IST timezone) |
| `limit` | Daily cap: 50000 (free) / 500000 (premium) |
| `remaining` | `max(0, limit - tokens_used)` - never negative |
| `requests` | AI calls made today |
| `resets_at` | Seconds until midnight IST |
| `upgrade_url` | Stripe link for free users; `null` for premium |

Poll this after each AI call or on window focus to keep the usage bar fresh.

---

## 10. Admin

All admin endpoints require `admin: true` Firebase custom claim.

### `PUT /admin/users/{uid}/plan`

**Request body:** `{ "plan": "premium" }`
**Response `200`:** `{ "uid": "uid-abc", "plan": "premium" }`

### `POST /admin/jobs`

**Request body:**
```json
{
  "title": "Backend Engineer",
  "company": "Acme Corp",
  "description": "We are looking for...",
  "location": "Remote",
  "job_type": "full_time",
  "category": "engineering",
  "apply_url": "https://acme.com/careers/123"
}
```
**Response `201`:** Full job object with `id` and `created_at`.

### `PATCH /admin/jobs/{job_id}`
Update any fields of a job posting.

### `DELETE /admin/jobs/{job_id}`
**Response:** `200 { "deleted": true }`

---

## 11. Rate Limiting (429)

When a user hits their daily token limit on `POST /resume/generate` or `POST /ats/check`:

```json
HTTP 429
{
  "detail": {
    "code": "limit_reached",
    "message": "You have used your daily AI limit. Upgrade to premium to continue.",
    "plan": "free",
    "used": 50000,
    "limit": 50000,
    "resets_at": 3600,
    "upgrade_url": "https://stripe.example.com"
  }
}
```

**Frontend handling:**
```js
if (res.status === 429) {
  const { detail } = await res.json();
  if (detail.code === "limit_reached") {
    showLimitModal({
      message: detail.message,
      resetsAt: detail.resets_at,    // show countdown timer
      upgradeUrl: detail.upgrade_url // null for premium users
    });
  }
}
```

---

## 12. Frontend State Machine - Resume Generation

```
User selects template
        |
        v
POST /resume/generate { template_id, extra_info, answers: [] }
        |
        |--- 429 --> Show limit modal (upgrade / countdown)
        |--- 404 --> "Please create your profile first"
        |--- 502 --> "AI error, please try again"
        |
        |--- status: "needs_info"
        |       |
        |       v
        |   Show questions form to user
        |       |
        |       v
        |   POST /resume/generate { ..., answers: [{question, answer}] }
        |       |-- loop back to top
        |
        +--- status: "ready"
                |
                v
           GET /resume/{resume_id}/pdf  --> download or preview
```

---

## 13. Frontend State Machine - ATS Check

```
User uploads file + optional JD
        |
        v
POST /ats/check (multipart/form-data)
        |
        |--- 429 --> Show limit modal
        |--- 413 --> "File too large (max 5 MB)"
        |--- 415 --> "Only PDF and DOCX are supported"
        |--- 422 --> "Could not extract text (scanned PDF?)"
        |--- 502 --> "AI error, please try again"
        |
        +--- 200 --> Display ATS results:
                       - Score gauge (0-100)
                       - Label badge (Poor / Fair / Good / Excellent)
                       - Breakdown table
                       - Matched / Missing keyword chips
                       - Strengths list
                       - Improvements list (sorted by priority)
```

---

## 14. Recommended UI Pages & Components

### Pages

| Route | Description |
|---|---|
| `/` | Landing / hero page |
| `/dashboard` | Overview: profile completion, recent resumes, usage bar |
| `/profile` | Edit profile form |
| `/templates` | Template gallery grid |
| `/resume/generate` | Step 1: pick template -> Step 2: extra info -> Step 3: answer questions -> Step 4: download |
| `/resume` | List of generated resumes with download buttons |
| `/ats` | Upload resume + paste JD -> results page |
| `/jobs` | Job board with filters |
| `/jobs/:id` | Job detail + apply button |
| `/usage` | Current plan, usage bar, upgrade CTA |
| `/admin` | Admin dashboard: manage jobs, set user plans |

### Key Components

| Component | Props / Notes |
|---|---|
| `UsageBar` | `used`, `limit`, `resets_at` - progress bar + countdown |
| `LimitModal` | `message`, `resets_at`, `upgradeUrl` - shown on 429 |
| `ATSScoreGauge` | `score` (0-100), `label` - circular gauge |
| `BreakdownTable` | `breakdown[]` - category, score/max, comment |
| `KeywordChips` | `matched[]`, `missing[]` - color-coded chips |
| `ImprovementsList` | `improvements[]` - sorted by priority, expandable |
| `QuestionForm` | `questions: string[]` - collect answers before retry |
| `ResumeCard` | `id`, `template_id`, `created_at` - download button |
| `JobCard` | `title`, `company`, `job_type`, `location`, `apply_url` |
| `TemplateCard` | `id`, `name`, `preview_url`, `required`, `optional` |

### Timezone / Countdown

`resets_at` is **seconds from now** (not a timestamp):
```js
const h = Math.floor(resets_at / 3600);
const m = Math.floor((resets_at % 3600) / 60);
// "Resets in 6h 23m"
```

---

## Quick Reference - All Endpoints

| Method | Path | Auth | Rate Limited | Description |
|---|---|---|---|---|
| GET | `/health` | No | No | App health |
| GET | `/health/db` | No | No | Firestore health |
| PUT | `/profile` | Yes | No | Save profile |
| GET | `/profile` | Yes | No | Get profile |
| DELETE | `/profile` | Yes | No | Delete profile |
| GET | `/templates` | Yes | No | List templates |
| GET | `/templates/{id}` | Yes | No | Get template |
| POST | `/resume/generate` | Yes | YES | Generate resume |
| GET | `/resume` | Yes | No | List resumes |
| GET | `/resume/{id}/pdf` | Yes | No | Download PDF |
| DELETE | `/resume/{id}` | Yes | No | Delete resume |
| POST | `/ats/check` | Yes | YES | ATS score check |
| GET | `/jobs` | Yes | No | List jobs |
| GET | `/jobs/{id}` | Yes | No | Get job |
| GET | `/usage/me` | Yes | No | My usage & plan |
| PUT | `/admin/users/{uid}/plan` | Admin | No | Set user plan |
| POST | `/admin/jobs` | Admin | No | Create job |
| PATCH | `/admin/jobs/{id}` | Admin | No | Update job |
| DELETE | `/admin/jobs/{id}` | Admin | No | Delete job |
