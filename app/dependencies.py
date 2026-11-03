import secrets
from typing import Annotated
from fastapi import Header, HTTPException
from app.config import settings

async def get_token_header(x_token: Annotated[str, Header()]):
    if not secrets.compare_digest(x_token, settings.admin_token.get_secret_value()):
        raise HTTPException(status_code=401, detail="X-Token header invalid")
