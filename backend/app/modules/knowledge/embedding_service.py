"""Generate embeddings for uploaded knowledge chunks."""

from functools import lru_cache

EMBEDDING_DIMENSIONS = 1024


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("BAAI/bge-m3", device="cpu")


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Attach normalized embeddings to prepared chunks."""

    if not chunks:
        raise ValueError("No chunks to embed")

    texts = [chunk["text"] for chunk in chunks]

    vectors = get_embedding_model().encode(
        texts,
        batch_size=4,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    result = []

    for chunk, vector in zip(chunks, vectors, strict=True):
        embedding = vector.tolist()

        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError("Invalid embedding dimensions")

        result.append(
            {
                **chunk,
                "embedding": embedding,
            }
        )

    return result
