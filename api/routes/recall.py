"""Recall endpoint for searching memory."""
from fastapi import APIRouter, Depends

from api.dependencies import get_flow_service
from services.flow_service import FlowService
from services.models import RecallRequest, RecallResponse

router = APIRouter()


@router.post("/recall", response_model=RecallResponse)
async def recall_context(
    request: RecallRequest,
    service: FlowService = Depends(get_flow_service),
) -> RecallResponse:
    """
    Search for relevant context and learnings.

    Uses semantic search via Backboard.io when available,
    falls back to local keyword search otherwise.

    **Example:**
    ```json
    {
        "query": "authentication",
        "tags": ["auth"],
        "limit": 10
    }
    ```
    """
    return await service.recall_context(request)
