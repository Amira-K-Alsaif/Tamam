
-- Tamam Knowledge Factory
-- Database migration

-- Enable pgvector
CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS vector
WITH SCHEMA extensions;

-- Documents
CREATE TABLE IF NOT EXISTS public.documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    department TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    updated_at DATE NOT NULL
);

-- Chunks and embeddings
CREATE TABLE IF NOT EXISTS public.chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL
        REFERENCES public.documents(id)
        ON DELETE CASCADE,
    section_title TEXT NOT NULL,
    page INTEGER,
    text TEXT NOT NULL,
    normalized_text TEXT,
    embedding extensions.vector(1024)
);

CREATE INDEX IF NOT EXISTS idx_chunks_document
ON public.chunks(document_id);

-- Security
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.documents FROM anon, authenticated;
REVOKE ALL ON public.chunks FROM anon, authenticated;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE
ON public.documents, public.chunks
TO service_role;

-- Semantic search
CREATE OR REPLACE FUNCTION public.match_chunks(
    query_embedding extensions.vector(1024),
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id TEXT,
    document_id TEXT,
    section_title TEXT,
    page INTEGER,
    content TEXT,
    similarity DOUBLE PRECISION
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = public, extensions
AS $$
    SELECT
        c.id,
        c.document_id,
        c.section_title,
        c.page,
        c.text AS content,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM public.chunks AS c
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT LEAST(GREATEST(match_count, 1), 20);
$$;

REVOKE ALL ON FUNCTION public.match_chunks(
    extensions.vector, INTEGER
) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.match_chunks(
    extensions.vector, INTEGER
) TO service_role;
