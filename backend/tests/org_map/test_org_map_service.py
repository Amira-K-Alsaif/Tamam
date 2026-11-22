import pytest

from app.modules.org_map import mock_data, service

VIEWER = mock_data.CURRENT_EMPLOYEE_ID


def test_overview_lists_five_departments_under_the_ceo():
    overview = service.get_overview(VIEWER)

    assert overview.ceo.full_name == "خالد الدوسري"
    assert [d.name for d in overview.departments] == [
        "الموارد البشرية",
        "تقنية المعلومات",
        "البيانات والتحليلات",
        "المالية",
        "العمليات",
    ]
    assert overview.employee_count == 214
    assert [d.id for d in overview.departments if d.is_mine] == ["dep-data"]
    assert overview.my_manager_id == "emp-002"


def test_department_lists_head_first_with_team_sizes():
    department = service.get_department("dep-data", VIEWER)

    assert department.headcount == 18
    assert [(t.name, t.size) for t in department.teams] == [
        ("البيانات والتحليلات", 8),
        ("هندسة البيانات", 7),
        ("الحوكمة", 3),
    ]
    assert department.members[0].full_name == "سارة القحطاني"
    assert department.members[0].is_department_head


def test_relations_to_the_viewer():
    members = {m.id: m.relation for m in service.get_department("dep-data", VIEWER).members}

    assert members["emp-002"] == "manager"
    assert members["emp-003"] == "mentor"
    assert members["emp-004"] == "self"
    assert members["emp-142"] is None


def test_person_shows_contact_topics_and_procedures():
    person = service.get_person("emp-002", VIEWER)

    assert person.contact_topics == ["اعتماد الإجازات", "موافقة صلاحية المستودع", "تقييم الأداء"]
    assert [(p.id, p.title) for p in person.procedures] == [
        ("proc-warehouse", "إجراء صلاحية مستودع البيانات")
    ]
    assert person.email == "sara.qahtani@nakhla.example"


def test_unknown_ids_raise_not_found():
    with pytest.raises(service.NotFoundError):
        service.get_department("nope", VIEWER)
    with pytest.raises(service.NotFoundError):
        service.get_person("nope", VIEWER)


def test_search_finds_who_approves_data_access():
    hits = service.search("مين أكلّم عن صلاحيات البيانات؟", VIEWER).hits

    assert hits[0].person.full_name == "سارة القحطاني"
    assert hits[0].matched_topic in {"موافقة صلاحية المستودع", "إجراء صلاحية مستودع البيانات"}


def test_search_ignores_hamza_and_taa_marbuta_differences():
    with_hamza = service.search("إجازة اضطرارية", VIEWER).hits
    without = service.search("اجازه اضطراريه", VIEWER).hits

    assert with_hamza[0].person.full_name == "مها العنزي"
    assert [h.person.id for h in without] == [h.person.id for h in with_hamza]


def test_search_never_returns_the_viewer_and_can_find_nothing():
    assert all(h.person.id != VIEWER for h in service.search("محللة بيانات", VIEWER).hits)
    assert service.search("عضوية النادي الرياضي", VIEWER).hits == []


def test_ids_match_module_5_and_the_procedure_catalog():
    # Module 5 sends people here by id, and the access approvers it names must be the ones
    # this map shows as responsible for that procedure.
    access_admin = service.get_person("emp-005", VIEWER)
    assert access_admin.job_title == "مسؤول الصلاحيات"
    assert {p.id for p in access_admin.procedures} == {"proc-system-access", "proc-vpn"}
    assert all(pid.startswith("proc-") for pid in mock_data.PROCEDURE_TITLES)
