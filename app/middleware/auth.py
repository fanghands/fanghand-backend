import time

from jose import JWTError, jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

# Routes that do not require authentication
PUBLIC_PATHS = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)

PUBLIC_PREFIXES = (
    "/webhooks",
)

# Public GET-only routes
PUBLIC_GET_PREFIXES = (
    "/api/v1/hands",
    "/api/v1/payments/burns",
)


class JWTMiddleware(BaseHTTPMiddleware):
    """Decode JWT from Authorization header and attach user_id to request.state."""

    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.wallet_address = None

        path = request.url.path
        method = request.method

        # Skip auth for public routes
        if path in PUBLIC_PATHS:
            return await call_next(request)

        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        if method == "GET":
            for prefix in PUBLIC_GET_PREFIXES:
                if path.startswith(prefix):
                    return await call_next(request)

        # Extract and validate token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            request.state.user_id = payload.get("sub")
            request.state.wallet_address = payload.get("wallet")
        except JWTError as exc:
            logger.debug("JWT decode failed: {}", str(exc))
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        if not request.state.user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing subject claim"},
            )

        return await call_next(request)
