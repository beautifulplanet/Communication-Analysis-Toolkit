from fastapi import APIRouter

from api.schemas import AskRequest, AskResponse
from api.services import get_case_agent

router = APIRouter()

@router.post("/cases/{case_id}/ask", response_model=AskResponse)
async def ask_question(case_id: str, req: AskRequest) -> AskResponse:
    """Ask a natural-language question about a case."""
    agent = get_case_agent(case_id)
    result = agent.ask(req.question)

    return AskResponse(
        answer=result.answer,
        layer=result.layer,
        confidence=result.confidence,
        evidence=result.evidence,
        messages_searched=(
            result.retrieval.total_searched if result.retrieval else 0
        ),
        filters_applied=(
            result.retrieval.filters_applied if result.retrieval else []
        ),
    )
