"""
Unified Application Entry Point

This file imports and registers all routes from microservices into a single app.
Use this for development when you want all services running together.

Individual services can still be run independently using their own main.py files.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

# Import routers from individual services
from backend.api_gateway.routes import auth

# Create unified app
app = FastAPI(
    title="OrchestrMator - Unified Application",
    description="All services in one application for development",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Register all routers from API Gateway
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])

# Future: Register routers from other services
# from backend.workflow_engine.routes import workflows
# app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.get("/")
async def root():
    """Unified application root"""
    return {
        "message": "OrchestrMator - Unified Application",
        "version": "1.0.0",
        "docs": "/api/docs",
        "services": ["api_gateway", "workflow_engine (future)", "scheduler (future)"]
    }

@app.get("/health")
async def health():
    """Global health check"""
    return {
        "status": "healthy",
        "mode": "unified"
    }