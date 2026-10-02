from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
def get_admin_metrics():
    return {"message": "Admin metrics endpoint"}
