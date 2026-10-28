from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis/", tags=["analysis"])
async def start_analysis():
    pass