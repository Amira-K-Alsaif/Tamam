"""Shared test data for the chat module. Tests never load a real model."""

import pytest

from app.modules.chat.chunking import Chunk


@pytest.fixture
def leave() -> Chunk:
    return Chunk(
        id="leave",
        document_id="doc-leave",
        document_title="سياسة الإجازات",
        section_title="الإجازة السنوية",
        page=4,
        text="إجازة سنوية مدتها ٢١ يوماً.",
    )


@pytest.fixture
def remote() -> Chunk:
    return Chunk(
        id="remote",
        document_id="doc-remote",
        document_title="سياسة العمل عن بعد",
        section_title="الأهلية",
        page=2,
        text="العمل عن بعد يومين في الأسبوع.",
    )


@pytest.fixture
def chunks(leave, remote) -> list[Chunk]:
    return [leave, remote]
