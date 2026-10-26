import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router
from app.api.v1.categories import router as categories_router
from app.api.v1.categories import admin_router as admin_categories_router
from app.api.v1.blogs import router as blogs_router
from app.api.v1.comments import router as comments_router
from app.api.v1.ratings import router as ratings_router

from app.db.session import engine
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.exceptions.handlers import register_exception_handlers

from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


configure_logging()

request_logger = logging.getLogger("app.requests")

app = FastAPI(title="Content Management Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(admin_categories_router, prefix="/api/v1")
app.include_router(blogs_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(ratings_router, prefix="/api/v1")



@app.get("/health")
def health_check():
    return {"status": "healthy"}



@app.get("/health/redis")
def redis_health_check():
    try:
        redis_client.ping()
        return {
            "status": "ok",
            "redis": "connected",
        }
    except Exception as exc:
        request_logger.exception("Redis health check failed")
        raise HTTPException(
            status_code=503,
            detail="Redis connection failed",
        ) from exc


@app.get("/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }
    except SQLAlchemyError as exc:
        request_logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from exc
