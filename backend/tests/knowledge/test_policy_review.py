"""Cited rule-mismatch review and read-only data quality regression tests."""

from app.modules.knowledge.policy_review import audit_knowledge_data, find_policy_conflicts


def _docs():
    return [
        {"id": "p1", "title": "سياسة الإجازة", "department": "الموارد البشرية", "status": "ready"},
        {"id": "p2", "title": "دليل الإجازة", "department": "الموارد البشرية", "status": "ready"},
    ]


def _chunks(a, b):
    return [
        {"id": "c1", "document_id": "p1", "section_title": "التقديم", "text": a},
        {"id": "c2", "document_id": "p2", "section_title": "التقديم", "text": b},
    ]


def test_numeric_policy_mismatch_includes_both_exact_excerpts():
    a = "يُرفع الطلب عبر بوابة الموارد البشرية قبل بداية الإجازة بأربعة عشر يومًا على الأقل."
    b = "يُرفع الطلب عبر بوابة الموارد البشرية قبل بداية الإجازة بسبعة أيام على الأقل."
    conflicts = find_policy_conflicts(_docs(), _chunks(a, b))
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "needs_review"
    assert conflicts[0]["values"] == [14, 7]
    assert conflicts[0]["unit"] == "day"
    assert conflicts[0]["sources"][0]["quote"] == a.rstrip(".")
    assert conflicts[0]["sources"][1]["quote"] == b.rstrip(".")


def test_no_mismatch_for_same_threshold():
    statement = "يقدم الموظف الطلب قبل بداية الاجازة بسبعة أيام على الأقل"
    assert find_policy_conflicts(_docs(), _chunks(statement, statement)) == []


def test_no_comparison_between_unrelated_departments():
    documents = _docs()
    documents[1]["department"] = "المالية"
    a = "يُرفع الطلب عبر بوابة الموارد البشرية قبل بداية الإجازة بأربعة عشر يومًا على الأقل"
    b = "يُرفع الطلب عبر بوابة الموارد البشرية قبل بداية الإجازة بسبعة أيام على الأقل"
    assert find_policy_conflicts(documents, _chunks(a, b)) == []


def test_ignores_archived_and_multi_threshold_passages():
    docs = _docs()
    docs[0]["status"] = "archived"
    a = "يستحق الموظف 21 يوما ثم 30 يوما بعد 5 سنوات"
    b = "يستحق الموظف 19 يوما ثم 22 يوما بعد 5 سنوات"
    assert find_policy_conflicts(docs, _chunks(a, b)) == []


def test_audit_flags_duplicates_orphans_and_empty_chunks_without_modifying():
    docs = _docs()
    chunks = [
        {"id": "c1", "document_id": "p1", "section_title": "الغرض", "text": "أهلًا"},
        {"id": "c2", "document_id": "p1", "section_title": "الغرض", "text": "اهلا"},
        {"id": "c3", "document_id": "gone", "section_title": "", "text": " "},
    ]
    before = [dict(x) for x in chunks]
    audit = audit_knowledge_data(docs, chunks)
    assert audit["mode"] == "read_only"
    assert audit["documents_count"] == 2
    assert audit["chunks_count"] == 3
    assert {x["type"] for x in audit["issues"]} == {
        "duplicate_chunk",
        "orphan_chunk",
        "empty_chunk",
        "missing_section_title",
    }
    assert chunks == before
