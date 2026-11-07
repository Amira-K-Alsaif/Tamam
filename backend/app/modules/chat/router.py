"""Ask about a procedure (RAG chat). Owned by one team member; see docs/team.md."""

from fastapi import APIRouter, HTTPException

from app.ai.llm import LLMNotConfiguredError

from . import service
from .schemas import AskRequest, AskResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        return service.answer(request.question)
    except LLMNotConfiguredError:
        raise HTTPException(status_code=503, detail="خدمة الإجابة غير مهيأة حالياً.") from None
