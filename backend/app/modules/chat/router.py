"""Ask about a procedure (RAG chat). Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

from .schemas import AskRequest, AskResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return AskResponse(
        answer="ما لقيت هذي المعلومة في وثائق الشركة.",
        found=False,
        sources=[],
    )