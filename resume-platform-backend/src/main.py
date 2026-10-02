from fastapi import FastAPI
from src.core.database import get_db

app = FastAPI()


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
