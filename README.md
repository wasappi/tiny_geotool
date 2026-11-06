# Tiny Geo Tool

Monthly vegetation-cover analysis from Sentinel-2 satellite imagery. Frame an area on a map, pick a month, and the app returns its land-cover composition (water, built-up / bare soil, sparse and dense vegetation), computed from cloud-free observations only.



## Features

- Select any area by moving the map; pick a month
- Searches the Sentinel-2 catalogue and reads only the pixels covering the area (no full-tile download)
- Masks clouds and cloud shadows per pixel, and skips observations where the area is mostly covered
- Classifies each pixel by NDVI and averages the composition over the month's clear observations
- Runs each analysis in the background and polls its status, so the page responds immediately and the map stays locked until the result arrives
- Shows the result as a doughnut chart, with every observation listed (including the excluded ones and why)
- Stores every analysis in PostgreSQL and lists the five most recent ones

## How it works

1. **Search.** The selected month and bounding box are sent to the [Earth Search](https://earth-search.aws.element84.com/v1) STAC API (collection `sentinel-2-c1-l2a`). Tiles with 60 % cloud cover or more are filtered out up front, and the first 3 matching items are kept.
2. **Coverage check.** Sentinel-2 is cut into overlapping 110 km tiles, and a tile can be mostly empty at the edge of the satellite's swath. Each item's data footprint must fully contain the area; otherwise it is skipped.
3. **Windowed reads.** The red (B04), near-infrared (B08) and scene classification (SCL) bands are Cloud-Optimized GeoTIFFs. The bounding box is reprojected from WGS84 to the tile's UTM zone, and only that window is read over HTTP with Rasterio.
4. **Cloud masking.** Tile-level cloud cover describes the whole tile, not the area, so clouds are measured in the area itself using the SCL band (nodata, saturated, cloud shadow, medium and high probability clouds, cirrus are masked). SCL is 20 m, so it is resampled to the 10 m grid with nearest neighbour, since its values are class codes. Observations with less than 80 % clear pixels are excluded.
5. **NDVI.** `NDVI = (B08 − B04) / (B08 + B04)`, computed on clear pixels, with bands cast to `float32` first (the source data is `uint16`, where the subtraction would wrap around).
6. **Classification.** Water `< 0`, built / bare soil `0–0.2`, sparse vegetation `0.2–0.6`, dense vegetation `≥ 0.6`.
7. **Monthly summary.** The class percentages are averaged over the clear observations (a mean, so the composition still adds up to 100 %), then the analysis and its observations are saved.

### Validation

Results were compared against an NDVI computed from a manual Copernicus Browser export of the same area and period.

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic, pydantic-settings |
| Geospatial | pystac-client, Rasterio (GDAL), NumPy, Shapely |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| Frontend | Jinja2 templates, HTMX, Bootstrap 5, Mapbox GL JS, Chart.js |
| Deployment | Docker, Kamal, behind Nginx Proxy Manager and Cloudflare |
| Tooling | uv |

## Project structure

```
app/
├── main.py              # FastAPI app, page and health-check (/up) routes
├── config.py            # settings from environment variables
├── database.py          # engine, session dependency
├── templating.py        # shared Jinja2 instance
├── models/              # Analysis, Observation
├── routers/             # HTTP layer: form parsing, validation, rendering
├── services/
│   ├── stac_client.py       # STAC search, coverage check
│   ├── raster_processor.py  # windowed reads, cloud masking, NDVI classes
│   ├── summary.py           # monthly average over clear observations
│   └── analysis.py          # runs an analysis and saves it
├── templates/           # page and HTMX partials
└── static/              # CSS and JavaScript (map, charts)
migrations/              # Alembic migrations
config/deploy.yml        # Kamal deployment
dataset/                 # Copernicus Browser export used for validation
```

Routers only handle HTTP (parsing and validating input, rendering templates); the analysis logic lives in `services/`.

## Running locally

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker, the [Bitwarden CLI](https://bitwarden.com/help/cli/) and `jq`.

```bash
git clone https://github.com/wasappi/tiny_geotool.git
cd tiny_geotool
uv sync
docker compose up -d   # PostgreSQL on localhost:5433
bin/env-sync           # writes .env from the Bitwarden item "geotool-dev"
```

`bin/env-sync` expects a Bitwarden item named `geotool-dev` with the custom fields `MAPBOX_PUBLIC_TOKEN` and `ADMIN_TOKEN`; it adds the local `DATABASE_URL` itself. Without Bitwarden, create `.env` by hand:

```
DATABASE_URL=postgresql+psycopg://geotool:geotool@localhost:5433/geotool
MAPBOX_PUBLIC_TOKEN=pk.…
ADMIN_TOKEN=…
```

Create the database schema and start the server:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000. The interactive API docs are at `/docs`.

## Deployment

The app is packaged as a Docker image and deployed with [Kamal](https://kamal-deploy.org/): `kamal deploy` builds the image from the last commit, pushes it to GitHub Container Registry, and swaps containers with zero downtime, using `/up` as the health check. PostgreSQL runs as a Kamal accessory on the same server. Database migrations run automatically when the container starts.

Secrets are fetched from Bitwarden at deploy time: [.kamal/secrets](.kamal/secrets) holds only the fetch commands and reads the item `geotool-prod` (fields `MAPBOX_PUBLIC_TOKEN`, `ADMIN_TOKEN`, `POSTGRES_PASSWORD`). `DATABASE_URL` is built from `POSTGRES_PASSWORD`, and the registry password comes from `gh auth token`. Deploying needs `kamal`, `bw`, `gh` logged in with the `write:packages` scope, SSH access to the server and `BW_ACCOUNT` set to the Bitwarden account email (used only if `bw` is logged out). The production Mapbox token is restricted to the deployed domain.

## Design choices

- **Filtering before results.** Tile-level metadata is only used as a pre-filter; clouds and coverage are measured in the selected area, and excluded observations stay visible with the reason.
- **Synchronous code.** pystac-client and Rasterio are blocking libraries, and the database is not the bottleneck, so endpoints are plain `def` functions run in FastAPI's thread pool, with synchronous SQLAlchemy.
- **Background analysis with polling.** Submitting the form validates the input, creates the analysis with status `processing` and returns at once; the work runs as a FastAPI `BackgroundTasks` job in its own database session and ends with status `done` or `failed` (with the error message). The page polls `/check-status/{id}` every 2 s with HTMX: the endpoint answers `204` (nothing to swap) while the analysis runs, then the result or error card, which replaces the polling element and stops the polling.
- **Summary stored once.** An analysis never changes after it is computed, so its summary is stored with it rather than recomputed on each view.

## Limitations and next steps

- **At most 3 observations per month.** The search keeps the first 3 catalogue items, so the monthly average may not use every pass of the month. Raising the cap is easy, but each item costs three remote reads.
- **Single tile only.** An area that no single tile covers is skipped; mosaicking neighbouring tiles is not implemented.
- **In-process background jobs.** `BackgroundTasks` runs in the web process, so an analysis in progress is lost if the container restarts or is redeployed, and its row stays `processing`. A job queue (arq, RQ or Celery) would make jobs durable and retryable; the status column and the polling would stay the same.
- **Fixed thresholds.** NDVI classes, the 60 % tile pre-filter and the 80 % clear threshold are fixed; they could become parameters.
- **Thin cirrus is masked** like other clouds, which is conservative; it could be tolerated with a correction.
- Change detection between months and a seasonal NDVI curve are natural extensions.

## Data attribution

Contains modified Copernicus Sentinel data 2026, accessed through [Earth Search](https://earth-search.aws.element84.com/v1) (Element 84). Map data © Mapbox © OpenStreetMap contributors.

## License

[Apache 2.0](LICENSE)
