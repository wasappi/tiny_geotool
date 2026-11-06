from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.stac_client import search
from app.services.summary import summarize
from app.models import Analysis, Observation
from app.database import SessionLocal
from app.models.analysis import AnalysisStatus


def run_analyse(analysis_id: int, coords: list[float], datetime_month: str):
    with SessionLocal() as db:
        analysis = db.get(Analysis, analysis_id)
        assert analysis is not None
        try:
            analysis.min_lon = coords[0]
            analysis.min_lat = coords[1]
            analysis.max_lon = coords[2]
            analysis.max_lat = coords[3]

            measures = search(coords=coords, datetime_month=datetime_month)["measures"]
            result = summarize(measures)

            analysis.usable_count = result["usable_count"]
            for k,v in (result["summary"] or {}).items():
                setattr(analysis, k, v)
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
                analysis.status = AnalysisStatus.DONE
                db.commit()
        except Exception as e:
            db.rollback()
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            db.commit()



