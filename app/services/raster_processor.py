from rasterio import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

def compute_ndvi(b04_url:str, b08_url:str, bbox:list[float]):
    """
    NDVI (Normalized Difference Vegetation index)
    B08 = Infra Red, B04 = Red
    NDVI = (BO8 - BO4) / (B08 + B04)
    """
    with rasterio.open(b04_url) as src:
        utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
        window = from_bounds(*utm_bounds, transform=src.transform)
        b04 = src.read(1, window=window, masked=True).astype("float32") # masked=True to mask nodata pixels
    with rasterio.open(b08_url) as src:
        utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
        window = from_bounds(*utm_bounds, transform=src.transform)
        b08 = src.read(1, window=window, masked=True).astype("float32") # masked=True to mask nodata pixels
    ndvi = (b08 - b04) / (b08 + b04)
    categories = {
        "water_pct":            ndvi < 0,
        "buit_bare_pct":     (ndvi >= 0) & (ndvi < 0.2),
        "sparse_veg_pct": (ndvi >= 0.2) & (ndvi < 0.6),
        "dense_veg_pct": ndvi >= 0.6,
    }
    breakdown = {name: float(mask.mean() * 100) for name, mask in categories.items()}
    return breakdown