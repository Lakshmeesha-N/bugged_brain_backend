from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_resumes():
    return {"message": "List resumes endpoint"}
