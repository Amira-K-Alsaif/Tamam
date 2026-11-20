from app.modules.chat.chunking import all_chunks, split_documents

DOCUMENT = {
    "id": "doc-test",
    "title": "وثيقة تجريبية",
    "sections": [
        {"title": "القسم الأول", "page": 1, "text": "فقرة قصيرة."},
        {"title": "القسم الثاني", "page": 2, "text": "كلمة " * 200},
    ],
}


def test_every_chunk_remembers_its_document_section_and_page():
    first = split_documents([DOCUMENT])[0]

    assert first.document_id == "doc-test"
    assert first.document_title == "وثيقة تجريبية"
    assert first.section_title == "القسم الأول"
    assert first.page == 1


def test_long_sections_are_split_into_several_chunks_with_unique_ids():
    chunks = split_documents([DOCUMENT])
    second_section = [chunk for chunk in chunks if chunk.page == 2]

    assert len(second_section) > 1
    assert all(len(chunk.text) <= 400 for chunk in second_section)
    assert len({chunk.id for chunk in chunks}) == len(chunks)


def test_the_company_documents_produce_chunks():
    assert len(all_chunks()) > 0
