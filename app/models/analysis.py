from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from sqlalchemy import func
# Import seen by editor but never run to avoid circular ref
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.observation import Observation

class Analysis(Base):
    __tablename__ = "analysis"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    month: Mapped[str]
    min_lon: Mapped[float]
    min_lat: Mapped[float]
    max_lon: Mapped[float]
    max_lat: Mapped[float]
    bbox: Mapped[str] 
    observations: Mapped[list[Observation]] = relationship(back_populates="summary", cascade="all, delete-orphan")

    # Summary
    usable_count: Mapped[int] = mapped_column(default=0)
    water_pct: Mapped[float | None]
    built_bare_pct: Mapped[float | None]
    sparse_veg_pct: Mapped[float | None]
    dense_veg_pct: Mapped[float | None]

