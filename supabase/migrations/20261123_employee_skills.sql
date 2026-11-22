-- Tamam employee skill profile, shared by onboarding (writes) and career (reads).
-- Contract: docs/team.md, "Employee skill profile".

CREATE TABLE IF NOT EXISTS public.employee_skills (
    employee_id TEXT NOT NULL,
    skill_id INT NOT NULL REFERENCES public.skills(id),
    level SMALLINT NOT NULL CHECK (level BETWEEN 0 AND 4),
    source TEXT NOT NULL CHECK (source IN ('cv', 'assessment')),
    evidence TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (employee_id, skill_id)
);

-- A profile is private to its employee. The backend writes with the service role; an
-- employee reading through Supabase sees only their own rows.
ALTER TABLE public.employee_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY employee_skills_owner_read ON public.employee_skills
    FOR SELECT USING (employee_id = auth.uid()::text);
