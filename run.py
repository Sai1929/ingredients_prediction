#!/usr/bin/env python3
"""Entry point for running the Recipe Ingredient Calculator API."""

import uvicorn

from app.config import get_settings


def main():
    """Run the FastAPI application with uvicorn."""
    settings = get_settings()

    gemini_status = "Configured" if settings.is_gemini_configured else "Not configured (set GEMINI_API_KEY)"
    print(f"""
============================================================
     Recipe Ingredient Calculator API  v{settings.app_version}
============================================================
  Server: http://{settings.host}:{settings.port}
  Docs:   http://localhost:{settings.port}/docs
  Health: http://localhost:{settings.port}/health
------------------------------------------------------------
  Gemini API: {gemini_status}
============================================================
    """)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main()
