import json
import os

import pytest

from app.modules.chat.corpus import CorpusNotPreparedError, load_chunks


@pytest.fixture
def manifest(tmp_path):
    path = tmp_path / "manifest.json"
    documents = [{"id": "remote-work", "title": "سياسة العمل عن بُعد"}]
    path.write_text(json.dumps(documents, ensure_ascii=False), encoding="utf-8")
    return path


def test_reads_each_chunk_with_its_document_title(tmp_path, manifest):
    chunks_file = tmp_path / "chunks.jsonl"
    row = {
        "id": "remote-work-c002",
        "document_id": "remote-work",
        "section_title": "عدد الأيام",
        "page": None,
        "text": "الحد الأقصى المعتمد يومان في الأسبوع.",
    }
    chunks_file.write_text(json.dumps(row, ensure_ascii=False) + "\n\n", encoding="utf-8")

    [chunk] = load_chunks(chunks_file, manifest)

    assert chunk.document_title == "سياسة العمل عن بُعد"
    assert chunk.section_title == "عدد الأيام"
    assert chunk.page is None


def test_explains_how_to_prepare_a_missing_chunk_file(tmp_path, manifest):
    with pytest.raises(CorpusNotPreparedError, match="knowledge.cli"):
        load_chunks(tmp_path / "missing.jsonl", manifest)


def test_the_repository_manifest_lists_every_document_once():
    from app.modules.chat.corpus import MANIFEST_FILE

    ids = [document["id"] for document in json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))]

    assert ids and len(ids) == len(set(ids))


def test_rereads_the_chunks_after_the_file_changes(monkeypatch, tmp_path, manifest):
    from app.modules.chat import corpus

    chunks_file = tmp_path / "chunks.jsonl"
    monkeypatch.setattr(corpus, "CHUNKS_FILE", chunks_file)
    monkeypatch.setattr(corpus, "MANIFEST_FILE", manifest)

    def write(text: str, modified_ns: int) -> None:
        row = {
            "id": "c1",
            "document_id": "remote-work",
            "section_title": "عدد الأيام",
            "text": text,
        }
        chunks_file.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        os.utime(chunks_file, ns=(modified_ns, modified_ns))

    write("يوم واحد في الأسبوع.", modified_ns=1_000_000_000)
    assert corpus.all_chunks()[0].text == "يوم واحد في الأسبوع."

    write("يومان في الأسبوع.", modified_ns=2_000_000_000)
    assert corpus.all_chunks()[0].text == "يومان في الأسبوع."
