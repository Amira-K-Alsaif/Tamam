"""Procedure catalog. Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/procedures", tags=["procedures"])
