"""Company map: departments, people, and who to contact about what. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from . import mock_data, service
from .schemas import DepartmentDetail, OrgOverview, PersonDetail, SearchResponse

router = APIRouter(prefix="/api/org-map", tags=["org-map"])

# The viewer is the mock employee until auth exists.
VIEWER_ID = mock_data.CURRENT_EMPLOYEE_ID


@router.get("/overview", response_model=OrgOverview)
def get_overview() -> OrgOverview:
    """The CEO and every department with its head and headcount."""
    return service.get_overview(VIEWER_ID)


@router.get("/departments/{department_id}", response_model=DepartmentDetail)
def get_department(department_id: str) -> DepartmentDetail:
    try:
        return service.get_department(department_id, VIEWER_ID)
    except service.NotFoundError:
        raise HTTPException(status_code=404, detail="القسم غير موجود") from None


@router.get("/people/{person_id}", response_model=PersonDetail)
def get_person(person_id: str) -> PersonDetail:
    try:
        return service.get_person(person_id, VIEWER_ID)
    except service.NotFoundError:
        raise HTTPException(status_code=404, detail="الشخص غير موجود") from None


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(min_length=2, max_length=200)) -> SearchResponse:
    """Answers "who do I talk to about X?"."""
    return service.search(q, VIEWER_ID)
