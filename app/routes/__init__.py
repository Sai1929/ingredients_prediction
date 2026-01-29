"""API route handlers."""

from .health import router as health_router
from .recipe import router as recipe_router

__all__ = ["health_router", "recipe_router"]
