from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Skip auth if no API_KEY configured (dev mode)
        if not API_KEY:
            return await call_next(request)

        # Check API key
        provided_key = request.headers.get("X-API-Key")
        if not provided_key or provided_key != API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

        return await call_next(request)


async def verify_api_key(request: Request) -> bool:
    if not API_KEY:
        return True

    provided_key = request.headers.get("X-API-Key")
    return provided_key == API_KEY
