from pystac_client import Client
from fastapi import HTTPException, Query
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
    for item in results.items():
        red_url = item.assets["red"].href
        nir_url = item.assets["nir"].href
        print(f"ID: {item.id} - Cloud cover: {item.properties['eo:cloud_cover']} % - Red: {red_url} - NIR: {nir_url}")
        compute_ndvi(red_url, nir_url, coords, item.id)
    
    # print('\n' + '='*40, flush=True)
    # print(f'DEBUG TARGET -> pystac search results: {results.matched} items found', flush=True)
    # print('='*40 + '\n', flush=True)
    # for item in results.items():
    #     print(f"ID: {item.id} - Cloud cover: {item.properties['eo:cloud_cover']}%")
    


# Output
# Brussels — June 2026
# date         clear   greenness
# 2026-06-03    96%     41.2%
# 2026-06-11    88%     39.8%
# 2026-06-18    23%     —   (too cloudy, skipped)
# 2026-06-26    99%     42.5%
# -----------------------------
# Monthly median (3 clear dates): 41.2%