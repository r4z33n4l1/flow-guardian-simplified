"""Capture endpoint for saving coding context."""
from fastapi import APIRouter, Depends

from api.dependencies import get_flow_service
from services.flow_service import FlowService
from services.models import CaptureRequest, CaptureResponse

router = APIRouter()


@router.post("/capture", response_model=CaptureResponse)
async def capture_context(
    request: CaptureRequest,
    service: FlowService = Depends(get_flow_service),
) -> CaptureResponse:
    """
    Capture current coding context.

    Stores context to Backboard.io (if configured) and local storage.
    Includes git state, summary, decisions, next steps, and blockers.

    **Example:**
    ```json
    {
        "summary": "Implementing OAuth2 refresh tokens",
        "decisions": ["Use JWT with 15-min access tokens", "Redis for token storage"],
        "next_steps": ["Add refresh endpoint", "Write integration tests"],
        "tags": ["auth", "oauth2"]
    }
    ```
    """
    return await service.capture_context(request)
