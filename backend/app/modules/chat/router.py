"""HTTP routes for the chat module (اسأل عن إجراء). Owned by Amira; see docs/team.md."""

from fastapi import APIRouter, HTTPException

from app.ai.llm import LLMNotConfiguredError

from . import service
from .schemas import AskRequest, AskResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Answers a question from the company documents, with its sources."""
    try:
        return service.answer(request.question)
    except LLMNotConfiguredError:
        # Tell the user the service is down without exposing configuration details.
        raise HTTPException(status_code=503, detail="خدمة الإجابة غير مهيأة حالياً.") from None
