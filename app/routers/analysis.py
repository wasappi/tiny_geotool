from fastapi import APIRouter, Query
from app.services.stac_client import search
from pydantic import AfterValidator
from datetime import datetime
from typing import Annotated

router = APIRouter()

def validate_month(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("month must be in YYYY-MM format, e.g. 2026-06")
    return value

Month = Annotated[str, Query(description="Month as YYYY-MM"), AfterValidator(validate_month)]

@router.get("/analysis/", tags=["analysis"])
def start_analysis(datetime_month:Month="2026-06", bbox:str="4.272994995117188, 50.798774416257544, 4.455299377441407, 50.885708708915175"):
    search(bbox=bbox, datetime_month=datetime_month)