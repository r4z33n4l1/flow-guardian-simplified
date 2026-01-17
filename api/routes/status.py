"""Status endpoint for Flow Guardian state."""
from fastapi import APIRouter, Depends

from api.dependencies import get_flow_service
from services.flow_service import FlowService
from services.models import StatusResponse

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status(
    service: FlowService = Depends(get_flow_service),
) -> StatusResponse:
    """
    Get current Flow Guardian status.

    Returns information about:
    - Current user
    - Last save time
    - Current git branch
    - Session and learning counts
    - Storage configuration status
    """
    return await service.get_status()
