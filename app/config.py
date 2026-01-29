"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find the project root directory (where run.py is located)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    app_name: str = "Recipe Ingredient Calculator API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Gemini API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.4
    gemini_top_p: float = 0.95
    gemini_top_k: int = 40
    gemini_max_output_tokens: int = 8192

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Rate Limiting Configuration
    rate_limit_recipe: str = "10/minute"
    rate_limit_health: str = "60/minute"
    rate_limit_cache: str = "30/minute"

    # Cache Configuration
    cache_max_size: int = 1000
    cache_ttl_seconds: int = 3600  # 1 hour default TTL

    # Security Configuration
    enable_security_headers: bool = True

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
