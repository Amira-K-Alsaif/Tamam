-- Knowledge factory: persisted policy events, suitable for an admin alert feed.
-- Run once through Supabase SQL Editor (after 20261107_knowledge.sql).
CREATE TABLE IF NOT EXISTS public.knowledge_change_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_title TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'updated', 'deleted')),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_events_changed_at
    ON public.knowledge_change_events (changed_at DESC);

ALTER TABLE public.knowledge_change_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.knowledge_change_events FROM anon, authenticated;
GRANT SELECT, INSERT ON public.knowledge_change_events TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.knowledge_change_events_id_seq TO service_role;

CREATE OR REPLACE FUNCTION public.log_knowledge_policy_event()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.kind = 'policy' AND OLD.status = 'ready' THEN
            INSERT INTO public.knowledge_change_events (document_id, document_title, event_type)
            VALUES (OLD.id, OLD.title, 'deleted');
        END IF;
        RETURN OLD;
    END IF;

    IF NEW.kind <> 'policy' THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'INSERT' THEN
        IF NEW.status = 'ready' THEN
            INSERT INTO public.knowledge_change_events (document_id, document_title, event_type)
            VALUES (NEW.id, NEW.title, 'created');
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.status = 'ready' AND OLD.status IS DISTINCT FROM 'ready' THEN
        -- Upload pipeline inserts as processing, then changes to ready.
        INSERT INTO public.knowledge_change_events (document_id, document_title, event_type)
        VALUES (NEW.id, NEW.title, 'created');
    ELSIF NEW.status = 'ready' AND OLD.status = 'ready'
        AND (NEW.updated_at IS DISTINCT FROM OLD.updated_at
             OR NEW.title IS DISTINCT FROM OLD.title) THEN
        -- Metadata updates on an existing ready policy.
        INSERT INTO public.knowledge_change_events (document_id, document_title, event_type)
        VALUES (NEW.id, NEW.title, 'updated');
    END IF;
    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.log_knowledge_policy_event() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS knowledge_policy_events ON public.documents;
CREATE TRIGGER knowledge_policy_events
AFTER INSERT OR UPDATE OR DELETE ON public.documents
FOR EACH ROW EXECUTE FUNCTION public.log_knowledge_policy_event();
