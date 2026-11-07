"""Prepare a local, inspectable chunk file from the fictional company corpus."""

import argparse
import json
from pathlib import Path

from app.modules.knowledge.normalization import normalize_arabic
from app.modules.knowledge.service import (
    build_chunks,
    extract_markdown,
    load_manifest,
    resolve_document_path,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = PROJECT_ROOT / "data/company/manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/processed/chunks.jsonl"


def prepare_corpus(manifest_path: Path, output_path: Path) -> tuple[int, int]:
    documents = load_manifest(manifest_path)
    rows = []
    for document in documents:
        path = resolve_document_path(document, manifest_path.parent)
        markdown = extract_markdown(path)
        for chunk in build_chunks(document, markdown):
            rows.append({**chunk.model_dump(), "normalized_text": normalize_arabic(chunk.text)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(documents), len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Tamam's fictional knowledge corpus")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    documents, chunks = prepare_corpus(args.manifest, args.output)
    print(f"Prepared {documents} documents and {chunks} source-linked chunks: {args.output}")


if __name__ == "__main__":
    main()
