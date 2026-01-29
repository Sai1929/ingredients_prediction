"""Gemini AI service for recipe generation."""

import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from app.config import Settings
from app.models.schemas import RecipeRequest

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Exception raised when Gemini API call fails."""

    def __init__(self, message: str, error_code: str = "GEMINI_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class GeminiService:
    """Service for interacting with Google Gemini AI."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._model = None
        self._configured = False

        if settings.is_gemini_configured:
            self._configure()

    def _configure(self) -> None:
        """Configure the Gemini API client."""
        try:
            genai.configure(api_key=self._settings.gemini_api_key)

            # Configure model with JSON output mode
            generation_config = genai.GenerationConfig(
                temperature=self._settings.gemini_temperature,
                top_p=self._settings.gemini_top_p,
                top_k=self._settings.gemini_top_k,
                max_output_tokens=self._settings.gemini_max_output_tokens,
                response_mime_type="application/json",
            )

            self._model = genai.GenerativeModel(
                self._settings.gemini_model,
                generation_config=generation_config,
            )
            self._configured = True
            logger.info(f"Gemini API configured with model: {self._settings.gemini_model}")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            self._configured = False

    @property
    def is_configured(self) -> bool:
        """Check if the Gemini service is properly configured."""
        return self._configured

    def _build_prompt(self, request: RecipeRequest) -> str:
        """Build the recipe generation prompt - optimized for minimal tokens."""
        extras = ""
        if request.cuisine_type:
            extras += f" Style:{request.cuisine_type}."
        if request.dietary_restrictions:
            extras += f" Diet:{','.join(request.dietary_restrictions)}."

        prompt = f"""Chef recipe: "{request.dish_name}" for {request.servings} servings.{extras}

SCALE: Protein 150g/person, Veg 120g/person, Grain 80g/person. Spices scale 1.5x when doubling. Liquids scale 80%.

UNITS: grams(solids), ml(liquids), tsp(<10g). Include oil,salt,water.

CATEGORIES: protein|vegetable|grain|dairy|spice|oil|condiment|other

Return JSON:{{"dish_name":"{request.dish_name}","servings":{request.servings},"total_prep_time_minutes":0,"cuisine_type":"","difficulty":"medium","ingredients":[{{"name":"","quantity":0,"unit":"grams","category":"","notes":""}}],"cooking_instructions":[""],"cooking_tips":"","nutritional_info":{{"calories_per_serving":0,"protein_grams":0,"carbs_grams":0,"fat_grams":0}},"estimated_cost":"$0"}}

Short clear steps. Pro tips. Valid JSON only."""
        return prompt

    def _parse_response(self, response_text: str) -> dict:
        """Parse and validate the Gemini response."""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Fix common JSON issues
        text = re.sub(r',(\s*[}\]])', r'\1', text)  # Remove trailing commas

        # Check if JSON is truncated (incomplete)
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')

        if open_brackets > 0 or open_braces > 0:
            logger.warning("Incomplete JSON detected. Attempting to fix...")

            # Check for unclosed string by counting unescaped quotes
            # Remove escaped quotes for counting
            temp = text.replace('\\"', '')
            quote_count = temp.count('"')

            if quote_count % 2 == 1:
                # Odd number of quotes means unclosed string
                # Find last quote and close the string
                text = text.rstrip()
                if not text.endswith('"'):
                    text += '"'

            # Clean up and close brackets/braces
            text = text.rstrip(',\n\t ')
            text += ']' * open_brackets
            text += '}' * open_braces

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response (first 1000 chars):\n{text[:1000]}")

            # Last resort: try to extract partial data
            try:
                # Find the last valid JSON object
                for i in range(len(text), 0, -1):
                    try:
                        partial = text[:i]
                        # Try to close it
                        partial = partial.rstrip(',\n\t ')
                        open_b = partial.count('{') - partial.count('}')
                        open_br = partial.count('[') - partial.count(']')
                        partial += ']' * open_br + '}' * open_b
                        result = json.loads(partial)
                        logger.warning("Recovered partial JSON data")
                        return result
                    except:
                        continue
            except:
                pass

            raise GeminiServiceError(
                "Failed to parse recipe data from AI.",
                error_code="JSON_PARSE_ERROR"
            )

    async def generate_recipe(self, request: RecipeRequest) -> dict:
        """Generate a recipe using Gemini AI."""
        if not self._configured:
            raise GeminiServiceError(
                "Gemini API key not configured.",
                error_code="NOT_CONFIGURED"
            )

        prompt = self._build_prompt(request)

        try:
            response = self._model.generate_content(prompt)

            if not response.text:
                raise GeminiServiceError("Empty response from AI", error_code="EMPTY_RESPONSE")

            recipe_data = self._parse_response(response.text)
            logger.info(f"Successfully generated recipe for {request.dish_name}")
            return recipe_data

        except GeminiServiceError:
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise GeminiServiceError(f"AI service error: {str(e)}", error_code="API_ERROR")
