from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["mapbox_token"] = settings.mapbox_api_key