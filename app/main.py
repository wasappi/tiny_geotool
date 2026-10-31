from __future__ import annotations
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routers import analysis
from app.internal import admin
from app.dependencies import get_query_token, get_token_header
from app.config import settings 
from fastapi.staticfiles import StaticFiles
from datetime import date
from app.templating import templates
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(
    lifespan=lifespan,
    title="GeoTIFF Analytics API",
    description="API to analyse tiff dataset to extract NDVI, Cloud coverage and other metrics",
    version="0.1")

app.include_router(analysis.router)
app.include_router(admin.router, dependencies=[Depends(get_token_header)])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    current_month = date.today().strftime("%Y-%m")
    return templates.TemplateResponse(request=request, name="index.html", context={"current_month": current_month})
