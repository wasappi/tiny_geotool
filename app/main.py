from __future__ import annotations
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routers import analysis
from app.internal import admin
from app.dependencies import get_query_token, get_token_header
from app.models.analysis import RasterAnalysis

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(
    dependencies=[Depends(get_query_token)],
    lifespan=lifespan,
    title="GeoTIFF Analytics API",
    description="API to analyse tiff dataset to extract NDVI, Cloud coverage and other metrics",
    version="0.1")

app.include_router(analysis.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "Hello from root route"}
