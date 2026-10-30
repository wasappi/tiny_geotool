from pystac_client import Client
from fastapi import HTTPException, Query
from shapely.geometry import shape, box
from app.services.raster_processor import compute_ndvi

client = Client.open("https://earth-search.aws.element84.com/v1")

def search(bbox:str, datetime_month: str, max_items:int=3, collections:list=["sentinel-2-c1-l2a"]):
    try:
        coords = [float(item) for item in bbox.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid bbox values")
    if len(coords) != 4:
        raise HTTPException(status_code=422, detail="invalid bbox size")
    results = client.search(
        max_items=max_items,
        collections=collections,
        bbox=coords,
        datetime=datetime_month,
        query={"eo:cloud_cover": {"lt": 60}} # Pre-filter to remove any dataset with too much clouds
    )
    search_area = box(*coords) 
    items = results.item_collection()
    candidates = [item for item in items if item.geometry is not None and shape(item.geometry).contains(search_area)] # Skip Empty tiles and tiles that do not contains our bounding box
    
    measures = []
    for item in candidates:
        props = item.properties
        red_url = item.assets["red"].href
        nir_url = item.assets["nir"].href
        stats = compute_ndvi(red_url, nir_url, coords)
        measures.append({
            "date": props["datetime"],
            "bbox": {
                "left": coords[0],
                "bottom": coords[1],
                "right": coords[2],
                "top": coords[3]
            },
            "item_id": item.id,
            "platform": props["platform"],
            "clouds": {
                "thin_cirrus_pct": props.get("s2:thin_cirrus_percentage"),
                "medium_proba_clouds_pct": props.get("s2:medium_proba_clouds_percentage"),
                "high_proba_clouds_pct": props.get("s2:high_proba_clouds_percentage"),
            },
            **stats,
        })
    return {"measures": measures}


# Output
# Brussels — June 2026
# date         clear   greenness
# 2026-06-03    96%     41.2%
# 2026-06-11    88%     39.8%
# 2026-06-18    23%     —   (too cloudy, skipped)
# 2026-06-26    99%     42.5%
# -----------------------------
# Monthly median (3 clear dates): 41.2%