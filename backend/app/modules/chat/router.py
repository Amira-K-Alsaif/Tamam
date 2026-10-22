"""Ask about a procedure (RAG chat). Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])
