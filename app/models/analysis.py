from __future__ import annotations
import math
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from sqlalchemy import func
# Import seen by editor but never run to avoid circular ref
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.observation import Observation

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    month: Mapped[str]
    min_lon: Mapped[float]
    min_lat: Mapped[float]
    max_lon: Mapped[float]
    max_lat: Mapped[float]
    observations: Mapped[list[Observation]] = relationship(back_populates="analysis", cascade="all, delete-orphan")

    # Summary
    usable_count: Mapped[int] = mapped_column(default=0)
    water_pct: Mapped[float | None]
    built_bare_pct: Mapped[float | None]
    sparse_veg_pct: Mapped[float | None]
    dense_veg_pct: Mapped[float | None]


    @property
    def month_label(self) -> str:
        return datetime.strptime(self.month, "%Y-%m").strftime("%B %Y")
    
    @property
    def center_lat(self) -> float:
        return (self.min_lat + self.max_lat) / 2

    @property
    def center_lon(self) -> float:
        return (self.min_lon + self.max_lon) / 2

    @property
    def height_km(self) -> float:
        return (self.max_lat - self.min_lat) * 111.32

    @property
    def width_km(self) -> float:
        return (self.max_lon - self.min_lon) * 111.32 * math.cos(math.radians(self.center_lat))