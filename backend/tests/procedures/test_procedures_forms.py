"""Company forms read from their documents, and the forms API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.procedures.forms import FormDocumentError, parse_form

client = TestClient(app)

_LEAVE_FORM = """# نموذج طلب إجازة سنوية

## الحقول

اسم الموظف، الرقم الوظيفي، تاريخ البداية، تاريخ النهاية، عدد الأيام، قائمة المهام، المدير المباشر.

## تعليمات

تُعبأ الحقول في بوابة الموارد البشرية.
"""


def parse(text: str = _LEAVE_FORM):
    return parse_form(
        document_id="leave-request-form",
        title="نموذج طلب إجازة سنوية",
        department="الموارد البشرية",
        text=text,
    )


def test_reads_every_field_in_order_without_the_final_period():
    labels = [field.label for field in parse().fields]

    assert labels == [
        "اسم الموظف",
        "الرقم الوظيفي",
        "تاريخ البداية",
        "تاريخ النهاية",
        "عدد الأيام",
        "قائمة المهام",
        "المدير المباشر",
    ]


def test_marks_the_fields_the_employee_profile_fills():
    prefill = {field.label: field.prefill_from for field in parse().fields}

    assert prefill["اسم الموظف"] == "full_name"
    assert prefill["الرقم الوظيفي"] == "employee_id"
    assert prefill["المدير المباشر"] == "manager_name"
    assert prefill["تاريخ البداية"] is None


def test_infers_the_kind_of_answer_from_the_label():
    kinds = {field.label: field.kind for field in parse().fields}

    assert kinds["تاريخ البداية"] == "date"
    assert kinds["عدد الأيام"] == "number"
    assert kinds["قائمة المهام"] == "long_text"
    assert kinds["اسم الموظف"] == "text"


def test_cites_the_fields_section_as_its_source():
    form = parse()

    assert form.source.section_title == "الحقول"
    assert form.source.quote.startswith("اسم الموظف، الرقم الوظيفي")
    assert form.instructions == "تُعبأ الحقول في بوابة الموارد البشرية."


def test_rejects_a_form_document_without_fields():
    with pytest.raises(FormDocumentError):
        parse("# نموذج\n\n## تعليمات\n\nأرسله للمدير.\n")


def test_lists_the_company_forms():
    response = client.get("/api/procedures/forms")

    assert response.status_code == 200
    ids = [form["id"] for form in response.json()]
    assert ids == ["leave-request-form", "handover-form"]


def test_returns_one_form():
    response = client.get("/api/procedures/forms/handover-form")

    assert response.status_code == 200
    assert response.json()["fields"][2]["label"] == "الزميل البديل"


def test_unknown_form_is_404_in_arabic():
    response = client.get("/api/procedures/forms/nope")

    assert response.status_code == 404
    assert response.json()["detail"] == "ما لقيت هذا النموذج."
