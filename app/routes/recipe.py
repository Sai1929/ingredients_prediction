"""Recipe calculation endpoints."""

import logging

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.exceptions import ServiceUnavailableError, InternalServerError
from app.models.schemas import RecipeRequest, RecipeResponse, CacheStatsResponse
from app.services.gemini import GeminiServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Recipe"])
limiter = Limiter(key_func=get_remote_address)

settings = get_settings()


@router.post("/recipe", response_model=RecipeResponse)
@limiter.limit(settings.rate_limit_recipe)
async def get_recipe(request: Request, recipe_request: RecipeRequest):
    """
    Calculate ingredient quantities for a recipe.

    Takes a dish name and number of servings, returns detailed recipe
    with ingredients, cooking instructions, nutritional info, and tips.

    Rate limit: 10 requests per minute per IP

    Args:
        recipe_request: Recipe calculation request with dish name and servings

    Returns:
        Complete recipe with scaled ingredients

    Raises:
        503: If Gemini API is not configured
        500: If AI service encounters an error
    """
    # Get services from app state
    cache_service = request.app.state.cache_service
    gemini_service = request.app.state.gemini_service

    # Check if Gemini is configured
    if not gemini_service.is_configured:
        raise ServiceUnavailableError(
            "Gemini API key not configured. Please set GEMINI_API_KEY environment variable.",
            details={"error_code": "GEMINI_NOT_CONFIGURED"},
        )

    # Check cache first
    cached_recipe = await cache_service.get_recipe(
        recipe_request.dish_name,
        recipe_request.servings,
        recipe_request.dietary_restrictions,
    )

    if cached_recipe:
        logger.info(f"Cache hit for {recipe_request.dish_name}")
        return RecipeResponse(**cached_recipe)

    # Generate recipe using Gemini
    try:
        recipe_data = await gemini_service.generate_recipe(recipe_request)

        # Validate response matches our model
        response = RecipeResponse(**recipe_data)

        # Cache the result
        await cache_service.set_recipe(
            recipe_request.dish_name,
            recipe_request.servings,
            recipe_data,
            recipe_request.dietary_restrictions,
            ttl=settings.cache_ttl_seconds,
        )

        return response

    except GeminiServiceError as e:
        logger.error(f"Gemini service error: {e.message}")
        if e.error_code == "NOT_CONFIGURED":
            raise ServiceUnavailableError(e.message)
        raise InternalServerError(
            message=e.message,
            details={"error_code": e.error_code},
        )
    except Exception as e:
        logger.error(f"Unexpected error generating recipe: {e}", exc_info=True)
        raise InternalServerError(
            message="Failed to generate recipe",
            details={"original_error": str(e)},
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
@limiter.limit(settings.rate_limit_cache)
async def cache_stats(request: Request):
    """
    Get cache statistics.

    Returns the number of cached recipes and a sample of cache keys.

    Rate limit: 30 requests per minute per IP
    """
    cache_service = request.app.state.cache_service
    stats = await cache_service.get_stats()

    return CacheStatsResponse(
        cached_recipes=stats["cached_recipes"],
        cache_keys=stats["cache_keys"],
        max_size=settings.cache_max_size,
    )


@router.delete("/cache/clear")
@limiter.limit(settings.rate_limit_cache)
async def clear_cache(request: Request):
    """
    Clear all cached recipes.

    This will force all subsequent requests to call the Gemini API.

    Rate limit: 30 requests per minute per IP
    """
    cache_service = request.app.state.cache_service
    await cache_service.clear()
    logger.info("Recipe cache cleared")

    return {"message": "Cache cleared successfully"}
