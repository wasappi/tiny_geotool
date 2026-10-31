from rasterio import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import numpy as np

# https://www.spatialworkflow.io/cloud-masking-explained/
# Good ressource, explain issues with clouds projecting dark gray zone considered as bare / built zone when it should not
# Avoid some bands such as 0, 1, 3, 8, 9 and 10 — no data, saturated, cloud shadow, both cloud classes and thin cirrus. Treat 2 (dark area) and 7 (unclassified) as decisions to test on your own scene.

# Sentinel-2 L2A scene classification
UNUSABLE = [0,   # no data
            1,   # saturated or defective
            3,   # cloud shadow
            8,   # cloud, medium probability
            9,   # cloud, high probability
            10]  # thin cirrus

def read_window(url: str, bbox: list[float], out_shape=None,
                resampling=Resampling.nearest, masked=True):
    """Read the part of a remote raster covering a WGS84 bbox."""
    with rasterio.open(url) as src:
        utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
        window = from_bounds(*utm_bounds, transform=src.transform)
        return src.read(1, window=window, out_shape=out_shape,
                        resampling=resampling, masked=masked)


def compute_ndvi(b04_url: str, b08_url: str, scl_url: str, bbox: list[float],
                 min_clear_pct: float = 80.0):
    """
    NDVI (Normalized Difference Vegetation Index)
    B08 = near infrared, B04 = red
    NDVI = (B08 - B04) / (B08 + B04)
    Cloudy pixels are masked using the scene classification layer (SCL).
    """
    b04 = read_window(b04_url, bbox).astype("float32")
    b08 = read_window(b08_url, bbox).astype("float32")

    # SCL is 20 m: resample it onto the 10 m grid of B04.
    # Nearest neighbour, because SCL values are class codes, not measurements.
    scl = read_window(scl_url, bbox, out_shape=b04.shape, masked=False)
    cloudy = np.isin(scl, UNUSABLE)

    ndvi = (b08 - b04) / (b08 + b04)
    ndvi = np.ma.masked_where(cloudy | np.ma.getmaskarray(ndvi), ndvi)

    aoi_clear_pct = float((~ndvi.mask).mean() * 100)
    if aoi_clear_pct < min_clear_pct:
        return {"usable": False, "aoi_clear_pct": aoi_clear_pct}

    categories = {
        "water_pct":      ndvi < 0,
        "built_bare_pct": (ndvi >= 0) & (ndvi < 0.2),
        "sparse_veg_pct": (ndvi >= 0.2) & (ndvi < 0.6),
        "dense_veg_pct":  ndvi >= 0.6,
    }
    breakdown = {name: float(mask.mean() * 100) for name, mask in categories.items()}

    return {"usable": True, "aoi_clear_pct": aoi_clear_pct, **breakdown}

# def compute_ndvi(b04_url:str, b08_url:str, bbox:list[float]):
#     """
#     NDVI (Normalized Difference Vegetation index)
#     B08 = Infra Red, B04 = Red
#     NDVI = (BO8 - BO4) / (B08 + B04)
#     """
#     with rasterio.open(b04_url) as src:
#         utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
#         window = from_bounds(*utm_bounds, transform=src.transform)
#         b04 = src.read(1, window=window, masked=True).astype("float32") # masked=True to mask nodata pixels
#     with rasterio.open(b08_url) as src:
#         utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
#         window = from_bounds(*utm_bounds, transform=src.transform)
#         b08 = src.read(1, window=window, masked=True).astype("float32") # masked=True to mask nodata pixels
#     ndvi = (b08 - b04) / (b08 + b04)
#     categories = {
#         "water_pct":            ndvi < 0,
#         "built_bare_pct":     (ndvi >= 0) & (ndvi < 0.2),
#         "sparse_veg_pct": (ndvi >= 0.2) & (ndvi < 0.6),
#         "dense_veg_pct": ndvi >= 0.6,
#     }
#     breakdown = {name: float(mask.mean() * 100) for name, mask in categories.items()}
#     return breakdown