"""Pydantic models for API request/response validation."""

from typing import List, Optional
from pydantic import BaseModel, Field
import re


class Ingredient(BaseModel):
    """Single ingredient with quantity and metadata."""

    name: str = Field(..., description="Name of the ingredient")
    quantity: float = Field(..., description="Amount of the ingredient")
    unit: str = Field(..., description="Unit of measurement")
    category: str = Field(
        ..., description="Category: protein, vegetable, spice, dairy, grain, condiment, other"
    )
    notes: Optional[str] = Field(None, description="Additional preparation notes")


class RecipeRequest(BaseModel):
    """Request model for recipe calculation."""

    dish_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the dish to calculate ingredients for",
    )
    servings: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of servings to calculate for",
    )
    cuisine_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of cuisine (e.g., Indian, Italian, Chinese)",
    )
    dietary_restrictions: Optional[List[str]] = Field(
        None,
        description="List of dietary restrictions (e.g., vegan, gluten-free)",
    )
    difficulty_level: Optional[str] = Field(
        None,
        description="Recipe difficulty level",
    )

    @classmethod
    def validate_dish_name(cls, v: str) -> str:
        """Validate dish name contains only safe characters."""
        if not re.match(r"^[\w\s\-\'\,\.]+$", v, re.UNICODE):
            raise ValueError("Dish name contains invalid characters")
        return v.strip()


class NutritionalInfo(BaseModel):
    """Nutritional information per serving."""

    calories_per_serving: Optional[int] = Field(None, description="Calories per serving")
    protein_grams: Optional[int] = Field(None, description="Protein in grams")
    carbs_grams: Optional[int] = Field(None, description="Carbohydrates in grams")
    fat_grams: Optional[int] = Field(None, description="Fat in grams")


class RecipeResponse(BaseModel):
    """Response model for recipe calculation."""

    dish_name: str = Field(..., description="Name of the dish")
    servings: int = Field(..., description="Number of servings")
    total_prep_time_minutes: int = Field(..., description="Total preparation time in minutes")
    cuisine_type: Optional[str] = Field(None, description="Type of cuisine")
    ingredients: List[Ingredient] = Field(..., description="List of ingredients with quantities")
    cooking_instructions: List[str] = Field(..., description="Step-by-step cooking instructions")
    cooking_tips: Optional[str] = Field(None, description="Professional cooking tips")
    nutritional_info: Optional[dict] = Field(None, description="Nutritional information per serving")
    estimated_cost: Optional[str] = Field(None, description="Estimated cost for ingredients")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Health status")
    gemini_api: str = Field(..., description="Gemini API configuration status")
    cache_size: int = Field(..., description="Number of cached recipes")
    timestamp: str = Field(..., description="Current server timestamp")
    version: str = Field(default="1.0.0", description="API version")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    cached_recipes: int = Field(..., description="Number of cached recipes")
    cache_keys: List[str] = Field(..., description="Sample of cache keys")
    max_size: int = Field(default=1000, description="Maximum cache size")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    message: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[dict] = Field(None, description="Additional error details")
