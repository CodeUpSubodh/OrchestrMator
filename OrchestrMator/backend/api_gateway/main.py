from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from backend.api_gateway.routes import auth

app = FastAPI(
    title="OrchestrMator API",
    description="Telecom Automation Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Register routers with proper prefix
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
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
    """Root endpoint"""
    return {
        "message": "OrchestrMator API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }
