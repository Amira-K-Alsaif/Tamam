"""Shared test data for the procedures module. Tests never call the real model."""

import json

import pytest

from app.modules.procedures import service

_REIMBURSEMENT_TEXT = """# إجراء تعويض مصاريف العمل

## المتطلبات

يُرفق الإيصال وتاريخ النفقة واسم المشروع أو سبب العمل.

## الخطوات

افتح بوابة المالية. اختر تعويض مصروفات. ارفع الإيصالات. أرسل الطلب للموافقة وتابع الحالة.

## المدة

المدة الإرشادية للمراجعة خمسة أيام عمل بعد اكتمال المستندات.
"""


@pytest.fixture
def reimbursement_text() -> str:
    return _REIMBURSEMENT_TEXT


@pytest.fixture
def model_reply():
    """Builds the JSON the model would return, with any field overridden."""

    def build(**overrides) -> str:
        procedure = {
            "summary": "تعويض المصروفات الموافق عليها لأغراض العمل.",
            "owner": None,
            "duration_text": "خمسة أيام عمل",
            "requirements": ["الإيصال", "تاريخ النفقة"],
            "forms": [],
            "steps": [
                {"order": 2, "title": "ارفع الإيصالات", "detail": "ارفع الإيصالات."},
                {"order": 1, "title": "افتح بوابة المالية", "detail": "افتح بوابة المالية."},
            ],
            "evidence": "اختر تعويض مصروفات",
        }
        return json.dumps({"procedure": procedure | overrides}, ensure_ascii=False)

    return build


@pytest.fixture
def catalog_file(tmp_path, monkeypatch):
    """Points the service at a temporary catalog with two procedures."""
    path = tmp_path / "procedures.json"
    items = [
        _procedure("reimbursements", "إجراء تعويض مصاريف العمل", "المالية", "تعويض المصروفات"),
        _procedure("vpn", "دليل تفعيل الاتصال الآمن VPN", "تقنية المعلومات", "طلب صلاحية VPN"),
    ]
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(service, "CATALOG_PATH", path)
    return path


def _procedure(id: str, title: str, department: str, summary: str) -> dict:
    return {
        "id": id,
        "title": title,
        "department": department,
        "summary": summary,
        "owner": None,
        "duration_text": None,
        "requirements": [],
        "forms": [],
        "steps": [{"order": 1, "title": "ابدأ", "detail": "ابدأ الطلب."}],
        "source": {"document_id": id, "document_title": title, "quote": "ابدأ الطلب."},
    }
