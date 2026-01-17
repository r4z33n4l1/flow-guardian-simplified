"""FastAPI dependencies for service injection."""
from fastapi import Request

from services.config import FlowConfig
from services.flow_service import FlowService


def get_flow_service(request: Request) -> FlowService:
    """Get FlowService instance with config from app state."""
    config: FlowConfig = request.app.state.config
    return FlowService(config)
