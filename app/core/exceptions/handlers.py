
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.custom_exceptions import AppException

logger = logging.getLogger(__name__)


def error_response(
    message: str,
    error_code: str,
    status_code: int,
    headers: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error_code": error_code,
        },
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return error_response(
            message=exc.message,
            error_code=exc.code,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "TOO_MANY_REQUESTS",
        }

        messages = {
            404: "Resource not found",
            405: "Method not allowed",
        }

        return error_response(
            message=messages.get(exc.status_code, str(exc.detail)),
            error_code=error_codes.get(exc.status_code, "HTTP_ERROR"),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception occurred for %s %s",
            request.method,
            request.url.path,
        )
        return error_response(
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500,
        )
