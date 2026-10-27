from pystac_client import Client
from shapely.geometry import shape, box
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
import rasterio
import numpy as np

client = Client.open("https://earth-search.aws.element84.com/v1")

bbox = [4.272994995117188, 50.798774416257544, 4.455299377441407, 50.885708708915175]

search = client.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox, # Same bouding box as my Brussels area
    datetime="2026-07-01/2026-07-30",
    max_items=30
)

# Affichage des résultats trouvés
items = search.item_collection()
print(f"{len(items)} images trouvées.")
for item in items:
    print(f"ID: {item.id} - Nuages: {item.properties['eo:cloud_cover']}%")



aoi = box(*bbox) # box(bbox[0], bbox[1], bbox[2], bbox[3])
candidates = [item for item in items if item.geometry is not None and shape(item.geometry).contains(aoi)] # Skip Empty tiles and tiles that do not contains our bounding box

if not candidates:
    raise Exception("No images found for this bouding box")

# If still several candidates (range of datetime over several days), puck the one with lowest cloud cover
best = min(candidates, key=lambda item: item.properties["eo:cloud_cover"])
print(f"Using {best.id} ({best.properties['eo:cloud_cover']}% clouds)")
print(best.properties.items())
print("------------")
print(best.assets.keys())
red_url = best.assets["red"].href
nir_url = best.assets["nir"].href
print(f"red (b04): {red_url}")
print(f"infra (b08): {nir_url}")

# Need to convert to degrees
with rasterio.open(red_url) as src:
    utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
    window = from_bounds(*utm_bounds, transform=src.transform)
    b04 = src.read(1, window=window, masked=True) # masked=True to ommit nan values

with rasterio.open(nir_url) as src:
    utm_bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
    window = from_bounds(*utm_bounds, transform=src.transform)
    b08 = src.read(1, window=window, masked=True)

ndvi = (b08 - b04) / (b08 + b04)
greenness = (ndvi >= 0.6).mean() * 100
print(f"Greenness: {greenness:.1f}%")