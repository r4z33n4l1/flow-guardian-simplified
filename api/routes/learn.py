"""Learn endpoint for storing insights."""
from fastapi import APIRouter, Depends

from api.dependencies import get_flow_service
from services.flow_service import FlowService
from services.models import LearnRequest, LearnResponse

router = APIRouter()


@router.post("/learn", response_model=LearnResponse)
async def store_learning(
    request: LearnRequest,
    service: FlowService = Depends(get_flow_service),
) -> LearnResponse:
    """
    Store a learning or insight for future reference.

    Set `share_with_team` to true to share with teammates.

    **Example:**
    ```json
    {
        "insight": "JWT timestamps are always in UTC, not local time",
        "tags": ["auth", "jwt", "gotcha"],
        "share_with_team": true
    }
    ```
    """
    return await service.store_learning(request)
