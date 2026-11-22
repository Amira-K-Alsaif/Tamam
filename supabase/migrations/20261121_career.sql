-- Tamam career path (مساري المهني)
-- Market data behind the title skill profiles and the gap analysis.
-- Seeded from backend/app/modules/career/data/ by `python -m app.modules.career.seed_supabase`.

-- Ids come from the generated data files, so they are plain ints, not serial.
CREATE TABLE IF NOT EXISTS public.job_titles (
    id INT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    ladder TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('junior', 'mid', 'senior', 'lead', 'manager')),
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    next_title_id INT REFERENCES public.job_titles(id),
    esco_occupation_uri TEXT
);

CREATE TABLE IF NOT EXISTS public.job_postings (
    id INT PRIMARY KEY,
    posting_code TEXT UNIQUE NOT NULL,
    job_title_id INT NOT NULL REFERENCES public.job_titles(id)
);

CREATE INDEX IF NOT EXISTS idx_job_postings_title
ON public.job_postings(job_title_id);

CREATE TABLE IF NOT EXISTS public.skills (
    id INT PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    esco_id TEXT UNIQUE,
    label_en TEXT NOT NULL,
    label_ar TEXT,
    skill_type TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS public.posting_skills (
    posting_id INT REFERENCES public.job_postings(id) ON DELETE CASCADE,
    skill_id INT REFERENCES public.skills(id),
    importance TEXT CHECK (importance IN ('required', 'preferred')),
    extraction_method TEXT
        CHECK (extraction_method IN ('manual', 'keyword', 'llm', 'embedding_match')),
    confidence NUMERIC(3, 2),
    source_span TEXT,
    PRIMARY KEY (posting_id, skill_id)
);

-- A plain view, so the profile follows posting_skills without a refresh step.
CREATE OR REPLACE VIEW public.title_skill_profile
WITH (security_invoker = on) AS
SELECT jp.job_title_id,
       ps.skill_id,
       count(*) AS postings_count,
       round(count(*)::numeric / t.total, 2) AS frequency,
       round(avg((ps.importance = 'required')::int), 2) AS required_ratio
FROM public.posting_skills ps
JOIN public.job_postings jp ON jp.id = ps.posting_id
JOIN (
    SELECT job_title_id, count(*) AS total
    FROM public.job_postings
    GROUP BY job_title_id
) t ON t.job_title_id = jp.job_title_id
GROUP BY jp.job_title_id, ps.skill_id, t.total;

-- Security: only the backend (service role) reads or writes these tables.
ALTER TABLE public.job_titles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_postings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posting_skills ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.job_titles, public.job_postings, public.skills, public.posting_skills,
    public.title_skill_profile FROM anon, authenticated;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE
ON public.job_titles, public.job_postings, public.skills, public.posting_skills
TO service_role;
GRANT SELECT ON public.title_skill_profile TO service_role;
