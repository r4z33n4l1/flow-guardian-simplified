"""Flow Guardian HTTP API Server.

FastAPI application providing REST API for Flow Guardian.
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import capture, recall, learn, team, status
from services.config import FlowConfig
from services.models import HealthResponse

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: initialize config
    app.state.config = FlowConfig.from_env()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Flow Guardian API",
    description="Persistent memory for AI coding sessions. "
    "Capture context, recall learnings, and share with your team.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check if the API server is healthy."""
    config = app.state.config

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        backboard_status="configured" if config.backboard_available else "not configured",
        cerebras_status="configured" if config.cerebras_available else "not configured",
    )


# Include route modules
app.include_router(capture.router, tags=["Context"])
app.include_router(recall.router, tags=["Memory"])
app.include_router(learn.router, tags=["Learning"])
app.include_router(team.router, tags=["Team"])
app.include_router(status.router, tags=["Status"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
