from fastapi import APIRouter, Depends, Form, Request, BackgroundTasks, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import cast, select
from sqlalchemy.orm import Session
from app.models.analysis import Analysis, AnalysisStatus
from app.services.stac_client import search
from pydantic import AfterValidator
from datetime import datetime
from typing import Annotated
from app.templating import templates
from app.services.summary import summarize
from app.services.analysis import run_analyse
from app.database import get_db
from typing import cast

router = APIRouter()

def validate_month(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("month must be in YYYY-MM format, e.g. 2026-06")
    return value

def validate_bbox(bbox: str) -> list[float]:
    try:
        coords = [float(item) for item in bbox.split(",")]
    except ValueError:
        raise ValueError("invalid bbox values")
    if len(coords) != 4:
        raise ValueError("invalid bbox size")
    return coords

Month = Annotated[str, Form(description="Month as YYYY-MM"), AfterValidator(validate_month)]
Bbox = Annotated[str, Form(description="min_lon,min_lat,max_lon,max_lat"), AfterValidator(validate_bbox)]

@router.post("/analysis", tags=["analysis"], response_class=HTMLResponse)
def start_analysis(request: Request, bbox:Bbox, datetime_month:Month, background_tasks: BackgroundTasks, db: Session=Depends(get_db)):
    analysis = Analysis(
        status=AnalysisStatus.PROCESSING,
        month=datetime_month,
        min_lon=bbox[0], min_lat=bbox[1],
        max_lon=bbox[2], max_lat=bbox[3],
    )
    db.add(analysis)
    db.commit()
    bbox_coords = cast(list[float], bbox) # Needed else run_alanyze expect a list[float] while bbox is typed as str in the validator
    background_tasks.add_task(run_analyse, analysis.id, bbox_coords, datetime_month)
    return templates.TemplateResponse(
        request=request,
        name="partials/measure_processing.html",
        context={"analysis_id": analysis.id},
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

@router.get("/check-status/{analysis_id}", tags=["analysis"], response_class=HTMLResponse)
def check_status(request: Request, analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        return templates.TemplateResponse(
        request=request,
        name="partials/error.html"
        )
    if analysis.status == AnalysisStatus.DONE:
        return templates.TemplateResponse(
            request=request,
            name="partials/measure.html",
            context={"analysis": analysis}
        )
    elif analysis.status in (AnalysisStatus.PENDING, AnalysisStatus.PROCESSING):
        return Response(status_code=204)
    else:
        return templates.TemplateResponse(
        request=request,
        name="partials/measure_error.html",
        context={"analysis": analysis}
        )
