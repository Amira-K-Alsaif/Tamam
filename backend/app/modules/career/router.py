"""Career path. Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/career", tags=["career"])
