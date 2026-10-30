from fastapi import APIRouter, Form
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

Month = Annotated[str, Form(description="Month as YYYY-MM"), AfterValidator(validate_month)]

@router.post("/analysis", tags=["analysis"])
def start_analysis(bbox:Annotated[str, Form()], datetime_month:Month):
    return search(bbox=bbox, datetime_month=datetime_month)