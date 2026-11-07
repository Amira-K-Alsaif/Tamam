
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client


def search_knowledge(question: str):
    # Load credentials from backend/.env
    backend_dir = Path(__file__).resolve().parents[3]
    load_dotenv(backend_dir / ".env")

    db = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SECRET_KEY"],
    )

    # Convert the question to an embedding
    model = SentenceTransformer("BAAI/bge-m3", device="cpu")
    embedding = model.encode(
        question,
        normalize_embeddings=True,
    )

    # Search the database
    result = db.rpc(
        "match_chunks",
        {
            "query_embedding": json.dumps(embedding.tolist()),
            "match_count": 3,
        },
    ).execute()

    return result.data


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "قبل كم يوم لازم أقدم طلب الإجازة؟"

    results = search_knowledge(question)

    print("\nQuestion:", question)

    for i, chunk in enumerate(results, start=1):
        print(f"\n--- Result {i} ---")
        print("Similarity:", round(chunk["similarity"], 4))
        print("Document:", chunk["document_id"])
        print("Section:", chunk["section_title"])
        print("Text:", chunk["content"])
