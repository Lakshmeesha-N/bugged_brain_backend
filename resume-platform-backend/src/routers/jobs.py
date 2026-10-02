from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_jobs():
    return {"message": "List jobs endpoint"}
