import json
from pathlib import Path

import pytest

from app.modules.knowledge.cli import DEFAULT_MANIFEST, prepare_corpus
from app.modules.knowledge.normalization import normalize_arabic
from app.modules.knowledge.schemas import Document
from app.modules.knowledge.service import (
    build_chunks,
    load_manifest,
    resolve_document_path,
)


def test_company_has_28_valid_mock_documents():
    docs = load_manifest(DEFAULT_MANIFEST)
    assert len(docs) == 28
    assert {doc.kind for doc in docs} == {"policy", "procedure", "form", "faq"}
    assert all(resolve_document_path(doc, DEFAULT_MANIFEST.parent).is_file() for doc in docs)


def test_arabic_normalization_matches_common_spelling_variants():
    assert normalize_arabic("إِجَازَة   الموظَّف") == normalize_arabic("اجازه الموظف")
    assert normalize_arabic("عَلَى") == normalize_arabic("علي")


def test_chunks_keep_source_and_section_without_changing_original_text():
    document = load_manifest(DEFAULT_MANIFEST)[0]
    content = "# عنوان\n\n## الاستحقاق\n\nإجازة مدفوعة لمدة 21 يومًا.\n\n## الطلب\n\nقبل 14 يومًا."
    chunks = build_chunks(document, content)
    assert len(chunks) == 2
    assert chunks[0].document_id == document.id
    assert chunks[0].section_title == "الاستحقاق"
    assert "إجازة" in chunks[0].text
    assert chunks[1].section_title == "الطلب"
    assert all(c.embedding is None for c in chunks)


def test_long_sections_split_into_bounded_chunks():
    doc = load_manifest(DEFAULT_MANIFEST)[0]
    chunks = build_chunks(doc, "## طويلة\n\n" + "هذا مقطع طويل " * 150, max_chars=180)
    assert len(chunks) > 1
    assert all(len(c.text) <= 180 for c in chunks)


def test_document_path_cannot_escape_company_directory(tmp_path: Path):
    document = Document(
        id="x",
        title="Demo",
        kind="policy",
        department="IT",
        file_path="../../secrets.md",
        status="ready",
        updated_at="2026-10-28",
    )
    with pytest.raises(ValueError, match="within data/company"):
        resolve_document_path(document, tmp_path)


def test_cli_writes_source_linked_jsonl(tmp_path: Path):
    output = tmp_path / "chunks.jsonl"
    docs, chunks = prepare_corpus(DEFAULT_MANIFEST, output)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert docs == 28
    assert chunks == len(rows)
    assert chunks >= 28
    assert all(row["normalized_text"] for row in rows)
    assert all(row["document_id"] and row["section_title"] for row in rows)


def test_evaluation_questions_are_grounded_in_fake_documents():
    eval_path = DEFAULT_MANIFEST.parents[1] / "eval/knowledge_questions.json"
    rows = json.loads(eval_path.read_text(encoding="utf-8"))
    docs = {doc.id: doc for doc in load_manifest(DEFAULT_MANIFEST)}
    assert len(rows) == 50
    assert len({row["id"] for row in rows}) == 50
    for row in rows:
        doc = docs[row["expected_document_id"]]
        text = resolve_document_path(doc, DEFAULT_MANIFEST.parent).read_text(encoding="utf-8")
        assert normalize_arabic(row["expected_answer_hint"]) in normalize_arabic(text)
