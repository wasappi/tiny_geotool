from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from app.services.stac_client import search
from pydantic import AfterValidator
from datetime import datetime
from typing import Annotated
from app.templating import templates
from app.services.summary import summarize

router = APIRouter()

def validate_month(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("month must be in YYYY-MM format, e.g. 2026-06")
    return value

Month = Annotated[str, Form(description="Month as YYYY-MM"), AfterValidator(validate_month)]

@router.post("/analysis", tags=["analysis"], response_class=HTMLResponse)
def start_analysis(request: Request, bbox:Annotated[str, Form()], datetime_month:Month):
    result = search(bbox=bbox, datetime_month=datetime_month)
    context = {
        "month": datetime_month,
        **result,                          # measures
        **summarize(result["measures"]),   # summary, usable_count
    }
    return templates.TemplateResponse(
        request=request,
        name="partials/measure.html",
        context=context,
    )