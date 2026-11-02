from __future__ import annotations
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from app.routers import analysis
from app.internal import admin
from app.dependencies import get_token_header
from fastapi.staticfiles import StaticFiles
from datetime import date, timedelta
from app.templating import templates
from app import models  # noqa: F401 — registers models on Base.metadata

app = FastAPI(
    title="GeoTIFF Analytics API",
    description="API to analyse tiff dataset to extract NDVI, Cloud coverage and other metrics",
    version="0.1")

app.include_router(analysis.router)
app.include_router(admin.router, dependencies=[Depends(get_token_header)])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    today = date.today()
    current_month = today.strftime("%Y-%m")
    default_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    return templates.TemplateResponse(request=request, name="index.html", context={"current_month": current_month, "default_month": default_month})

@app.get("/up")
def up():
    return {"status": "ok"}