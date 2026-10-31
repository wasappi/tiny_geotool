from __future__ import annotations
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
# Import seen by editor but never run to avoid circular ref
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.analysis import Analysis

class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(primary_key=True)
    water_pct: Mapped[float | None] 
    built_bare_pct: Mapped[float | None] 
    sparse_veg_pct: Mapped[float | None] 
    dense_veg_pct: Mapped[float | None] 
    aoi_clear_pct: Mapped[float]
    platform: Mapped[str]
    observed_at: Mapped[datetime]
    raster_id: Mapped[str]
    usable: Mapped[bool]
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analysis.id"), index=True)
    analysis: Mapped[Analysis] = relationship(back_populates="observations")
    
