"""Procedure map (knowledge graph). Owned by one team member; see docs/team.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/procedure-map", tags=["procedure-map"])
