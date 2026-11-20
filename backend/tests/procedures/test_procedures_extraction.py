"""extract_procedure(), with the language model faked."""

import pytest

from app.ai import llm
from app.modules.procedures.extraction import ExtractionError, extract_procedure


def extract(monkeypatch, reply: str, text: str):
    monkeypatch.setattr(llm, "generate", lambda system, user: reply)
    return extract_procedure(
        document_id="reimbursements",
        title="إجراء تعويض مصاريف العمل",
        department="المالية",
        text=text,
    )


def test_builds_a_procedure_with_ordered_steps_and_its_source(
    monkeypatch, model_reply, reimbursement_text
):
    procedure = extract(monkeypatch, model_reply(), reimbursement_text)

    assert procedure.id == "reimbursements"
    assert procedure.department == "المالية"
    assert [step.order for step in procedure.steps] == [1, 2]
    assert procedure.source.quote == "اختر تعويض مصروفات"
    assert procedure.source.section_title == "الخطوات"


def test_accepts_json_wrapped_in_a_code_fence(monkeypatch, model_reply, reimbursement_text):
    procedure = extract(monkeypatch, f"```json\n{model_reply()}\n```", reimbursement_text)

    assert procedure is not None


def test_matches_the_document_despite_different_alef_forms(
    monkeypatch, model_reply, reimbursement_text
):
    procedure = extract(monkeypatch, model_reply(evidence="ارفع الايصالات"), reimbursement_text)

    assert procedure is not None


def test_returns_none_when_the_model_finds_no_procedure(monkeypatch, reimbursement_text):
    assert extract(monkeypatch, '{"procedure": null}', reimbursement_text) is None


@pytest.mark.parametrize("reply", ["هذا ليس JSON", '{"procedure": {"summary": "x"}}'])
def test_rejects_output_that_is_not_a_valid_procedure(monkeypatch, reimbursement_text, reply):
    with pytest.raises(ExtractionError):
        extract(monkeypatch, reply, reimbursement_text)


@pytest.mark.parametrize(
    "invented",
    [
        {"forms": ["نموذج FN-07"]},
        {"duration_text": "ثلاثة أيام عمل"},
        {"owner": "إدارة الخزينة"},
        {"evidence": "تُصرف المبالغ خلال يومين"},
    ],
)
def test_rejects_text_that_is_not_in_the_document(
    monkeypatch, model_reply, reimbursement_text, invented
):
    with pytest.raises(ExtractionError):
        extract(monkeypatch, model_reply(**invented), reimbursement_text)
