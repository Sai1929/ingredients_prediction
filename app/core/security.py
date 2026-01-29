"""Security middleware and CORS configuration."""

import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import Settings

logger = logging.getLogger(__name__)


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Configure CORS middleware with settings."""
    # Allow all origins in development (when file:// is used)
    # In production, use specific origins from settings
    origins = settings.cors_origins
    if "*" not in origins:
        # Add wildcard for development (file:// access)
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,  # Must be False when allow_origins is ["*"]
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    logger.info(f"CORS configured with origins: {origins}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response


def configure_security_headers(app: FastAPI, settings: Settings) -> None:
    """Configure security headers middleware."""
    if settings.enable_security_headers:
        app.add_middleware(SecurityHeadersMiddleware)
        logger.info("Security headers middleware enabled")
