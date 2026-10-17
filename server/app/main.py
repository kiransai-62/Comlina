# server/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-ID", "x-request-id", "Accept"],
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

@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "comlina-api",
        "version": settings.VERSION,
        "meta_api_version": settings.META_GRAPH_API_VERSION
    }
