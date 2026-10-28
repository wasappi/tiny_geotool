from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class RasterAnalysis(Base):
    """TODO: Red value, Nir value, NDVI compute, Cloud coverage, ..."""
    __tablename__ = "raster_analysis"
    id: Mapped[int] = mapped_column(primary_key=True)
    