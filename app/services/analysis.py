from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.stac_client import search
from app.services.summary import summarize
from app.models import Analysis, Observation

def run_analyse(bbox:str, datetime_month: str, db: Session):
    try:
        coords = [float(item) for item in bbox.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid bbox values")
    if len(coords) != 4:
        raise HTTPException(status_code=422, detail="invalid bbox size")

    measures = search(coords=coords, datetime_month=datetime_month)["measures"]
    result = summarize(measures)

    analysis = Analysis(
        month=datetime_month,
        min_lon=coords[0], min_lat=coords[1], max_lon=coords[2], max_lat=coords[3],
        usable_count=result["usable_count"],
        **(result["summary"] or {}),
    )

    for m in measures:
        analysis.observations.append(Observation(
            observed_at=datetime.fromisoformat(m["date"]),
            raster_id=m["item_id"],
            platform=m["platform"],
            usable=m["usable"],
            aoi_clear_pct=m["aoi_clear_pct"],
            water_pct=m.get("water_pct"),
            built_bare_pct=m.get("built_bare_pct"),
            sparse_veg_pct=m.get("sparse_veg_pct"),
            dense_veg_pct=m.get("dense_veg_pct"),
        ))

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis