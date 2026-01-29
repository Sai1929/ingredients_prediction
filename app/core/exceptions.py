"""Custom exception handlers and error responses."""

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom API error with structured response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[dict] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(404, message, "NOT_FOUND", details)


class BadRequestError(APIError):
    """Bad request error."""

    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(400, message, "BAD_REQUEST", details)


class ServiceUnavailableError(APIError):
    """Service unavailable error."""

    def __init__(
        self, message: str = "Service temporarily unavailable", details: Optional[dict] = None
    ):
        super().__init__(503, message, "SERVICE_UNAVAILABLE", details)


class InternalServerError(APIError):
    """Internal server error."""

    def __init__(
        self, message: str = "Internal server error", details: Optional[dict] = None
    ):
        super().__init__(500, message, "INTERNAL_ERROR", details)


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle custom API errors."""
        logger.warning(
            f"API Error: {exc.error_code} - {exc.message}",
            extra={"path": request.url.path, "details": exc.details},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle standard HTTP exceptions."""
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        error_code = error_codes.get(exc.status_code, "HTTP_ERROR")

        logger.warning(
            f"HTTP Exception: {exc.status_code} - {exc.detail}",
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=str(exc.detail),
                error_code=error_code,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({"field": field, "message": error["msg"]})

        logger.warning(
            f"Validation Error: {errors}",
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Request validation failed",
                error_code="VALIDATION_ERROR",
                details={"errors": errors},
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions."""
        # Log the full exception for debugging
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={"path": request.url.path},
        )

        # Return a generic error response (don't leak internal details)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
            ).model_dump(),
        )
