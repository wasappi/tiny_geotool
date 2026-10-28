from __future__ import annotations
import typer
import rasterio
import numpy as np
from rasterio.transform import Affine
from pathlib import Path
import matplotlib.pyplot as plt

def main():
    print("Hello from tiny-geotool!")
    # Read
    dataset = rasterio.open('dataset/output_hh.tif')
    # Dataset attributes and georeferencing
    print(f"{dataset.name}")
    print(f"{dataset.mode}")
    print(f"{dataset.closed}")
    print(f"{dataset.count}")
    print(f"{dataset.width} - {dataset.height}") # pixels reprsented as colums wide x rows height
    bands = {i: dtype for i, dtype in zip(dataset.indexes, dataset.dtypes)}
    print(f"{bands}") 
    print(f"bounds : {dataset.bounds}") # spatial bounding box
    print(f"{dataset.transform}") # affine 2D matrix
    print(f"{dataset.transform * (0,0)}") # get top left corner
    print(f"{dataset.transform * (dataset.width, dataset.height)}") # coordinates relative to origin of the dataset coordinate reference system (crs)
    print(f"{dataset.crs}") # specific refernce system (eg EPSG:4326)

    # Reading raster data
    print(f"{dataset.indexes}")
    band1 = dataset.read(1) # Data from a raster band can be accessed by the band index number (indexed from 1)
    print(f"{band1}") # return a numpy array
    print(f"{band1[dataset.width // 2, dataset.height // 2]}") # access central point of the dataset
    x, y = (dataset.bounds.left + 0.05, dataset.bounds.top - 0.03 ) # spatial coordinates shifted by ~3.5 km east, ~3.3 km south≠
    row, col = dataset.index(x,y) # coordinates → pixel
    print(f"row: {row}, col: {col}")
    lat, long = dataset.xy(row, col) # pixel → spatial coordinates (centre of that pixel)
    print(f"lat: {lat}, long: {long}")
    print(f"{band1[row, col]}")
    center_x, center_y = dataset.xy(dataset.height // 2, dataset.width // 2)
    print(f"center coordinates : {center_x}, {center_y}")

    write()
    # Write

def write():

    # The fictional field for this example consists of the difference of two Gaussian distributions and is represented by the array Z (2 depresions on a map)
    x = np.linspace(-4.0, 4.0, 240)
    y = np.linspace(-3.0, 3.0, 180)[::-1]
    X, Y = np.meshgrid(x, y)
    Z1 = np.exp(-2 * np.log(2) * ((X - 0.5) ** 2 + (Y - 0.5) ** 2) / 1 ** 2)
    Z2 = np.exp(-3 * np.log(2) * ((X + 0.5) ** 2 + (Y + 0.5) ** 2) / 2.5 ** 2)
    Z = 10.0 * (Z2 - Z1)

    res = (x[-1] - x[0]) / 240.0
    transform = Affine.translation(x[0] - res / 2, y[0] + res / 2) * Affine.scale(res, -res)

    new_dataset = rasterio.open(
        '/tmp/new.tif', #filename
        'w', # write mode
        driver='GTiff', # format driver
        height=Z.shape[0],
        width=Z.shape[1],
        count=1,
        dtype=Z.dtype,
        crs='+proj=latlong',
        transform=transform
    )

    new_dataset.write(Z, 1) # To copy the grid to the opened dataset, call the new dataset’s DatasetWriter.write() method with the grid and target band number as arguments
    new_dataset.close()


app = typer.Typer()


@app.command()
def info(path: Path):
    """prints the CRS, bounds, resolution, number of bands, data type and nodata value."""
    dataset = rasterio.open(path)
    print("Image Info")
    print(f"CRS: {dataset.crs}")
    print(f"Bounds: {dataset.bounds}")
    print(f"Resolution: {dataset.width} x {dataset.height}")
    print(f"Bands: {dataset.count}")
    print(f"Data type: {dataset.dtypes}")
    print(f"Nodata: {dataset.nodata}")


    # sentinel2_dir = Path("dataset/Sentinel-2/2026_10_06")
    # for file in sentinel2_dir.iterdir():
    #     dataset = rasterio.open(sentinel2_dir/file.name)
    #     print("##################")
    #     print(f"Image Info : {file.name}")
    #     print(f"CRS: {dataset.crs}")
    #     print(f"Bounds: {dataset.bounds}")
    #     print(f"Resolution: {dataset.width} x {dataset.height}")
    #     print(f"Bands: {dataset.count}")
    #     print(f"Data type: {dataset.dtypes}")
    #     print(f"Nodata: {dataset.nodata}")
    #     print("##################\n")

SENTINEL_DIR = Path("dataset/Sentinel-2/2026_10_06")

@app.command()
def create_ndvi():
    """
    NDVI (Normalized Difference Vegetation index)
    B08 = Infra Red, B04 = Red
    NDVI = (BO8 - BO4) / (B08 + B04)
    """
    with rasterio.open(SENTINEL_DIR/"B04.tiff") as src:
        print("Opening BO4 dataset")
        b04 = src.read(1) # get numpy array repr
        profile = src.profile # Contains all the raster data, will be updated with ndvi data

    with rasterio.open(SENTINEL_DIR/"B08.tiff") as src:
        print("Opening B08 dataset")
        b08 = src.read(1) # get numpy array repr

    # Caution, check for division by 0 and apply nan instead
    denominator = (b08 + b04)
    ndvi = np.where(denominator == 0, np.nan, (b08 - b04) / denominator)

    profile.update(dtype="float32", count=1, nodata=np.nan)
    with rasterio.open("dataset/Sentinel-2/2026_10_06/compute_ndvi.tiff", "w", **profile) as dst:
        dst.write(ndvi.astype("float32"), 1)

@app.command()
def read_ndvi():
    with rasterio.open(SENTINEL_DIR/"compute_ndvi.tiff") as src:
        ndvi = src.read(1, masked=True) # masked=True removes nan pixels from calculation
    greenness_percentage = np.mean(ndvi >= 0.6) * 100
    print(f"greeness percentage : {greenness_percentage}")

@app.command()
def preview(path: Path, output: Path):
    """Render a single-band raster to a PNG."""
    with rasterio.open(path) as src:
        array = src.read(1, masked=True)
    plt.imsave(output, array, cmap="RdYlGn", vmin=-1, vmax=1)

@app.command()
def peak():
    print("Peak point")
    dataset = rasterio.open("dataset/output_hh.tif")
    np_array = dataset.read(1)
    max_point = np_array.max()
    print(f"max point value: {max_point}")
    max_point_inside_np_array = np_array.argmax()
    print(f"max point position (inside np array): {max_point_inside_np_array}")
    row, col = np.unravel_index(max_point_inside_np_array, np_array.shape)
    print(f"max point row,col position {row} {col}")
    print(f"max point spation position {dataset.xy(row, col)}")

if __name__ == "__main__":
    app()    

