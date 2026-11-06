from app.modules.onboarding.mock_data import (
    ACCESS_ITEMS,
    ASSESSMENT_RESULTS,
    CURRENT_EMPLOYEE_ID,
    EMPLOYEE_ACCESS,
    EMPLOYEES,
)


def test_ids_are_unique():
    assert len({e.id for e in EMPLOYEES}) == len(EMPLOYEES)
    assert len({a.id for a in ACCESS_ITEMS}) == len(ACCESS_ITEMS)


def test_references_point_to_existing_records():
    employee_ids = {e.id for e in EMPLOYEES}
    access_ids = {a.id for a in ACCESS_ITEMS}

    assert CURRENT_EMPLOYEE_ID in employee_ids
    for e in EMPLOYEES:
        assert e.manager_id is None or e.manager_id in employee_ids
    for row in EMPLOYEE_ACCESS:
        assert row.employee_id in employee_ids
        assert row.access_item_id in access_ids
    for result in ASSESSMENT_RESULTS:
        assert result.employee_id in employee_ids
