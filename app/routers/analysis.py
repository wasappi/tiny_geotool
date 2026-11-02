from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.services.stac_client import search
from pydantic import AfterValidator
from datetime import datetime
from typing import Annotated
from app.templating import templates
from app.services.summary import summarize
from app.services.analysis import run_analyse
from app.database import get_db

router = APIRouter()

def validate_month(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("month must be in YYYY-MM format, e.g. 2026-06")
    return value

Month = Annotated[str, Form(description="Month as YYYY-MM"), AfterValidator(validate_month)]

@router.post("/analysis", tags=["analysis"], response_class=HTMLResponse)
def start_analysis(request: Request, bbox:Annotated[str, Form()], datetime_month:Month, db: Session=Depends(get_db)):
    analysis = run_analyse(bbox=bbox, datetime_month=datetime_month, db=db)
    return templates.TemplateResponse(
        request=request,
        name="partials/measure.html",
        context={"analysis": analysis},
    )

@router.get("/last_analyses", tags=["analysis"], response_class=HTMLResponse)
def get_latest_analyses(request: Request, db: Session=Depends(get_db)):
    stmt = select(Analysis).order_by(Analysis.created_at.desc()).limit(5)
    last_analyses = db.scalars(stmt).all()
    return templates.TemplateResponse(
        request=request,
        name="partials/analysis_list_item.html",
        context={"last_analyses": last_analyses}
    )