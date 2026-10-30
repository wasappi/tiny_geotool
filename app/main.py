from __future__ import annotations
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routers import analysis
from app.internal import admin
from app.dependencies import get_query_token, get_token_header

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

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
