"""Extract the procedure catalog from the fictional company's procedure documents.

Calls the real language model, so it needs TAMAM_GOOGLE_API_KEY in backend/.env.
Review data/company/procedures.json before committing it.
"""

import argparse
import json
import sys
from pathlib import Path

from .extraction import ExtractionError, extract_procedure
from .service import CATALOG_PATH, PROJECT_ROOT

DEFAULT_MANIFEST = PROJECT_ROOT / "data/company/manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=CATALOG_PATH)
    args = parser.parse_args()

    procedures, failed = [], []
    for entry in json.loads(args.manifest.read_text("utf-8")):
        if entry["kind"] != "procedure":
            continue
        text = (args.manifest.parent / entry["file_path"]).read_text("utf-8")
        try:
            procedure = extract_procedure(
                document_id=entry["id"],
                title=entry["title"],
                department=entry["department"],
                text=text,
            )
        except ExtractionError as error:
            failed.append(f"{entry['id']}: {error}")
            continue
        if procedure is None:
            failed.append(f"{entry['id']}: the model found no procedure")
            continue
        procedures.append(procedure.model_dump(mode="json"))

    args.output.write_text(
        json.dumps(procedures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Extracted {len(procedures)} procedures into {args.output}")
    for line in failed:
        print(f"FAILED {line}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
