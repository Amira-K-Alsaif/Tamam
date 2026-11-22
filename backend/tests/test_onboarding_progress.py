import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.onboarding.mock_data import DEMO_EMPLOYEE_IDS
from app.modules.onboarding.service import build_progress, build_roadmap, build_team

pytestmark = pytest.mark.usefixtures("new_hires_assessed")

client = TestClient(app)


def test_demo_employees_have_different_paths():
    new_hires = DEMO_EMPLOYEE_IDS[:3]
    percents = {build_progress(e).percent for e in new_hires}
    lengths = {sum(len(w.items) for w in build_roadmap(e).weeks) for e in new_hires}

    assert len(percents) == 3
    assert len(lengths) == 3


def test_progress_counts_active_access_and_passed_topics():
    progress = build_progress("emp-004")

    assert (progress.access_active, progress.access_total) == (2, 5)
    assert (progress.topics_passed, progress.topics_total) == (1, 5)
    assert progress.percent == 30


def test_badges_follow_progress():
    done = {b.id for b in build_progress("emp-003").badges if b.earned}
    started = {b.id for b in build_progress("emp-007").badges if b.earned}

    assert done == {"first-step", "ready", "half-way", "policies", "tamam"}
    assert started == {"first-step"}


def test_team_is_sorted_by_progress_with_next_step():
    team = build_team("emp-002")
    percents = [member.progress.percent for member in team]

    assert [m.employee.id for m in team] == ["emp-004", "emp-006", "emp-003"]
    assert percents == sorted(percents)
    assert team[0].next_step == "الشبكة الخاصة (VPN)"
    assert team[-1].next_step is None


def test_routes_accept_a_demo_employee():
    assert client.get("/api/onboarding/me?employee_id=emp-007").json()["id"] == "emp-007"
    assert client.get("/api/onboarding/progress?employee_id=emp-006").json()["percent"] == 80
    assert len(client.get("/api/onboarding/team?employee_id=emp-002").json()) == 3
    assert client.get("/api/onboarding/team").json() == []
    assert len(client.get("/api/onboarding/demo-employees").json()) == 4


def test_only_demo_employees_can_be_viewed():
    assert client.get("/api/onboarding/roadmap?employee_id=emp-999").status_code == 404
    assert client.get("/api/onboarding/roadmap?employee_id=emp-001").status_code == 404


def test_access_items_link_to_real_procedures():
    access = [i for w in build_roadmap("emp-004").weeks for i in w.items if i.kind == "access"]

    assert {i.procedure_id for i in access} == {"proc-vpn", "proc-warehouse", "proc-procurement"}
