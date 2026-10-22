"""Knowledge factory (documents and ingestion). Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
