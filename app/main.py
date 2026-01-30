"""FastAPI application factory."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import Settings, get_settings
from app.core.security import configure_cors, configure_security_headers
from app.core.exceptions import configure_exception_handlers
from app.routes import health_router, recipe_router
from app.services.cache import InMemoryCache, CacheService
from app.services.gemini import GeminiService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(settings: Settings = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        settings: Application settings. If None, uses default settings.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered ingredient quantity calculator using Google Gemini",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else "/docs",
        redoc_url="/redoc" if settings.debug else "/redoc",
    )

    # Configure rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure middleware (order matters!)
    # 1. GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 2. Security headers
    configure_security_headers(app, settings)

    # 3. CORS
    configure_cors(app, settings)

    # Configure exception handlers
    configure_exception_handlers(app)

    # Initialize services
    cache = InMemoryCache(
        max_size=settings.cache_max_size,
        default_ttl=settings.cache_ttl_seconds,
    )
    cache_service = CacheService(cache)
    gemini_service = GeminiService(settings)

    # Store services in app state for access in routes
    app.state.cache_service = cache_service
    app.state.gemini_service = gemini_service
    app.state.settings = settings

    # Register routers
    app.include_router(health_router)
    app.include_router(recipe_router)

    # Serve static files (CSS, JS, etc.)
    frontend_dir = Path(__file__).parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        # Serve index.html at root
        @app.get("/", include_in_schema=False)
        async def serve_frontend():
            return FileResponse(str(frontend_dir / "index.html"))

    # Log startup info
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Gemini API: {'configured' if gemini_service.is_configured else 'not configured'}")
        logger.info(f"CORS origins: {settings.cors_origins}")
        logger.info(f"Cache max size: {settings.cache_max_size}")
        logger.info(f"Rate limit (recipe): {settings.rate_limit_recipe}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")

    return app


# Create default app instance for uvicorn
app = create_app()
