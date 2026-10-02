from fastapi import APIRouter

router = APIRouter()

@router.post("/score")
def calculate_ats_score():
    return {"message": "Calculate ATS score endpoint"}
