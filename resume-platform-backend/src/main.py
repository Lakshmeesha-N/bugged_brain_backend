from fastapi import FastAPI
from src.core.database import get_db
from src.routers.admin_jobs import router as admin_jobs_router
from src.routers.admin_users import router as admin_users_router
from src.routers.ats import router as ats_router
from src.routers.jobs import router as jobs_router
from src.routers.profile import router as profile_router
from src.routers.resume import router as resume_router
from src.routers.templates import router as templates_router
from src.routers.usage import router as usage_router

app = FastAPI()

app.include_router(profile_router)
app.include_router(templates_router)
app.include_router(resume_router)
app.include_router(ats_router)
app.include_router(jobs_router)
app.include_router(admin_jobs_router)
app.include_router(admin_users_router)
app.include_router(usage_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        db = get_db()
        # Read one document from "health_check" collection (missing document is fine)
        _ = db.collection("health_check").document("ping").get()
        return {"db": "connected"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}
