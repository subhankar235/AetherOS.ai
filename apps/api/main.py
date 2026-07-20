# The entry point of the FastAPI application. Creates the app, adds middleware, registers exception handlers, includes routers, and exposes the /health endpoint.

import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import AppError
from core.logging import get_request_id, setup_logging, LoggingASGIMiddleware
from routers import webhooks

# Initialize structured logging
setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger("main")

# Instantiate FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AetherOS Core API Server",
    debug=settings.DEBUG,
)

# Startup event to initialize vector collections
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Qdrant collections on startup...")
    try:
        from integrations.qdrant_client import qdrant_client
        await qdrant_client.init_collections()
        logger.info("Qdrant collections initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collections on startup: {str(e)}")

    logger.info("Starting WebSocket event broadcaster...")
    try:
        from websocket.events import event_broadcaster
        await event_broadcaster.start()
        logger.info("WebSocket event broadcaster started.")
    except Exception as e:
        logger.error(f"Failed to start WebSocket event broadcaster: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping WebSocket event broadcaster...")
    try:
        from websocket.events import event_broadcaster
        await event_broadcaster.stop()
        logger.info("WebSocket event broadcaster stopped.")
    except Exception as e:
        logger.error(f"Error stopping WebSocket event broadcaster: {str(e)}")

# Register CORS middleware (locked to known origins from settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register ASGI logging middleware to propagate request context
app.add_middleware(LoggingASGIMiddleware)

# Register Exception Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = get_request_id()
    logger.warning(
        f"Application error: {exc.code} - {exc.message}",
        extra={"code": exc.code, "details": exc.details}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "details": exc.details
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id()
    errors = exc.errors()
    message = "Request validation failed"
    if errors:
        msg = errors[0].get("msg")
        loc = ".".join(str(l) for l in errors[0].get("loc", []))
        message = f"Validation failed: {msg} at {loc}"

    logger.warning(
        f"Validation error: {message}",
        extra={"errors": errors}
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "request_id": request_id,
                "details": {"errors": errors}
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id()
    logger.exception(f"Unhandled system error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id
            }
        }
    )

# Health endpoint (Checks DB + Redis + Qdrant connectivity, degrading gracefully)
@app.get("/health")
async def health_check():
    db_status = "healthy"
    redis_status = "healthy"
    qdrant_status = "healthy"

    # 1. Check DB Connectivity
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        engine = create_async_engine(settings.DATABASE_URL)
        
        async def check_db():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        
        await asyncio.wait_for(check_db(), timeout=2.0)
        await engine.dispose()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Health Check: Database connection failed: {str(e)}")

    # 2. Check Redis Connectivity
    try:
        import redis.asyncio as aioredis
        
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await asyncio.wait_for(r.ping(), timeout=2.0)
        await r.close()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
        logger.error(f"Health Check: Redis connection failed: {str(e)}")

    # 3. Check Qdrant Connectivity
    try:
        from qdrant_client import AsyncQdrantClient

        if settings.QDRANT_URL:
            qc = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=2)
            await asyncio.wait_for(qc.get_collections(), timeout=2.0)
            if hasattr(qc, "close"):
                await qc.close()
        else:
            qdrant_status = "unhealthy: QDRANT_URL not configured"
    except Exception as e:
        qdrant_status = f"unhealthy: {str(e)}"
        logger.error(f"Health Check: Qdrant connection failed: {str(e)}")

    # Determine overall status
    overall_status = "healthy"
    if "unhealthy" in db_status or "unhealthy" in redis_status or "unhealthy" in qdrant_status:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "qdrant": qdrant_status
        }
    }

# Mount Routers
app.include_router(webhooks.router)

from routers import integrations, inbox, knowledge, payments, dashboard, command_center, calendar, research, playbooks, vip_contacts, settings
from websocket import router as websocket_router
app.include_router(integrations.router)
app.include_router(inbox.router)
app.include_router(knowledge.router)
app.include_router(payments.router)
app.include_router(dashboard.router)
app.include_router(command_center.router)
app.include_router(calendar.router)
app.include_router(research.router)
app.include_router(playbooks.router)
app.include_router(vip_contacts.router)
app.include_router(settings.router)
app.include_router(websocket_router)

from fastapi import APIRouter, Depends
from core.deps import get_current_user

router = APIRouter()

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email
    }

app.include_router(router)