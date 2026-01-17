"""Team endpoint for searching shared knowledge."""
from fastapi import APIRouter, Depends

from api.dependencies import get_flow_service
from services.flow_service import FlowService
from services.models import TeamQueryRequest, TeamQueryResponse

router = APIRouter()


@router.post("/team", response_model=TeamQueryResponse)
async def query_team(
    request: TeamQueryRequest,
    service: FlowService = Depends(get_flow_service),
) -> TeamQueryResponse:
    """
    Search the team's shared knowledge base.

    Returns learnings and insights shared by team members.

    **Example:**
    ```json
    {
        "query": "rate limiting best practices",
        "limit": 10
    }
    ```
    """
    return await service.query_team(request)
