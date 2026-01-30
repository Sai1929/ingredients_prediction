"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])
limiter = Limiter(key_func=get_remote_address)

settings = get_settings()


@router.get("/health", response_model=HealthResponse)
@limiter.limit(settings.rate_limit_health)
async def health_check(request: Request):
    """
    Detailed health check endpoint.

    Returns:
        - Health status
        - Gemini API configuration status
        - Cache statistics
        - Current timestamp

    Rate limit: 60 requests per minute per IP
    """
    # Get cache service from app state
    cache_service = request.app.state.cache_service
    cache_size = await cache_service._cache.size()

    # Check Gemini configuration
    gemini_service = request.app.state.gemini_service
    gemini_status = "configured" if gemini_service.is_configured else "not_configured"

    return HealthResponse(
        status="healthy",
        gemini_api=gemini_status,
        cache_size=cache_size,
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
    )
