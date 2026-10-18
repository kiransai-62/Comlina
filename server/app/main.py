# server/app/main.py
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings

logger = logging.getLogger("comlina_api")
from app.core.database import init_db
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    PayloadSizeLimitMiddleware,
    AttackFilterMiddleware,
    ApiRateLimitMiddleware,
)
from app.api.auth import router as auth_router
from app.api.workspaces import router as workspaces_router
from app.api.automations import router as automations_router
from app.api.contacts import router as contacts_router
from app.api.conversations import router as conversations_router
from app.api.analytics import router as analytics_router
from app.api.instagram import router as instagram_router
from app.api.webhooks import router as webhooks_router
from app.api.payments import router as payments_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup: verify database tables
    await init_db()
    yield
    # Application shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
)

# 1. Security Headers (Outermost: guarantees OWASP headers on every response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Payload Size Limiting (Rejects oversized request bodies > 2MB)
app.add_middleware(PayloadSizeLimitMiddleware)

# 3. API Rate Limiting (Sliding-window rate limiter per client IP)
app.add_middleware(ApiRateLimitMiddleware)

# 4. Attack Signature & Bot Filter (Blocks injection attempts and automated scanners)
app.add_middleware(AttackFilterMiddleware)

# 5. CORS configuration
# Explicit origins only (wildcards strictly rejected) and credentials disabled for Bearer auth
cors_origins = [o for o in settings.CORS_ORIGINS if o and o != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=getattr(settings, "CORS_ALLOW_CREDENTIALS", False),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-ID", "x-request-id", "Accept"],
)

# Global Generic Exception Handlers to prevent stack trace leaks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    logger.error(f"[SERVER UNHANDLED ERROR] req_id={req_id} path={request.url.path} error={exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": req_id,
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    detail = exc.detail if isinstance(exc.detail, str) else "Request error"
    if exc.status_code >= 500:
        logger.error(f"[SERVER HTTP ERROR] req_id={req_id} status={exc.status_code} path={request.url.path} error={detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Server Error",
                "message": "A server error occurred. Please try again later.",
                "request_id": req_id,
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": detail,
            "message": detail,
            "request_id": req_id,
        },
        headers=getattr(exc, "headers", None)
    )

# Mount API Routers
app.include_router(webhooks_router) # Mounts /webhooks/instagram
app.include_router(webhooks_router, prefix="/api") # Mounts /api/webhooks/instagram
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(workspaces_router, prefix=settings.API_V1_STR)
app.include_router(automations_router, prefix=settings.API_V1_STR)
app.include_router(contacts_router, prefix=settings.API_V1_STR)
app.include_router(conversations_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(instagram_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)

@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route(f"{settings.API_V1_STR}/health", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/api/v1/health", methods=["GET", "HEAD"], tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "comlina-api",
        "version": settings.VERSION,
        "meta_api_version": settings.META_GRAPH_API_VERSION
    }

