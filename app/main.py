import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.middleware import setup_middlewares
from app.shared.exceptions import BaseAppException

# Import modular routers
from app.modules.auth.router import router as auth_router
from app.modules.profile.router import router as profile_router
from app.modules.users.router import router as users_router
from app.modules.workspaces.router import router as workspaces_router
from app.modules.tickets.router import router as tickets_router
from app.modules.devices.router import router as devices_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="s247 Platform — Service tickets and technical diagnostic telemetry backend",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Setup global middlewares (CORS)
setup_middlewares(app)


# Standardized global exception handler
@app.exception_handler(BaseAppException)
async def base_app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "error": {
                "code": exc.error_code,
                "field": exc.field,
                "message": exc.message,
            }
        },
    )


@app.get("/health", tags=["Monitoring"], summary="Application health check")
def health_check():
    """Health check endpoint for Docker probes and orchestrators."""
    return {"status": "ok", "app": settings.PROJECT_NAME}


# API Routers mounted with /v1 prefix
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(auth_router)  # /auth alias for machine client compatibility
app.include_router(profile_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(workspaces_router, prefix=settings.API_PREFIX)
app.include_router(tickets_router, prefix=settings.API_PREFIX)
app.include_router(devices_router, prefix=settings.API_PREFIX)
