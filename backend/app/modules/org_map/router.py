"""Company map: departments, people, and who to contact about what. See docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/org-map", tags=["org-map"])
