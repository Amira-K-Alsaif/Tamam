import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

# Project paths
ROOT = Path(__file__).resolve().parents[4]
INPUT = ROOT / "data/processed/chunks.jsonl"
OUTPUT = ROOT / "data/processed/chunks_embedded.jsonl"

# 1. Load prepared chunks
with INPUT.open(encoding="utf-8") as file:
    chunks = [json.loads(line) for line in file if line.strip()]

print(f"Loaded {len(chunks)} chunks")

# 2. Load the embedding model
model = SentenceTransformer("BAAI/bge-m3", device="cpu")

# 3. Generate embeddings from original text
texts = [chunk["text"] for chunk in chunks]

vectors = model.encode(
    texts,
    batch_size=4,
    normalize_embeddings=True,
    show_progress_bar=True,
)

# 4. Save vectors with their source information
with OUTPUT.open("w", encoding="utf-8") as file:
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk["embedding"] = vector.tolist()
        file.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print("Embeddings saved successfully!")
print("Total chunks:", len(chunks))
print("Vector dimensions:", len(vectors[0]))
print("Output:", OUTPUT)
