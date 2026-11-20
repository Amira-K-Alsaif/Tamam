// Career module API. Shapes match backend/app/modules/career/schemas.py.
import { apiGet } from '../../lib/api'

export type JobTitle = {
  id: number
  code: string
  ladder: string
  level: string
  name_ar: string
  name_en: string
  next_title_id: number | null
  postings_count: number
}

export type GapSkill = {
  skill_id: number
  label_ar: string
  label_en: string
  market_frequency: number
  expected_level: number
  employee_level: number
}

export type MissingSkill = GapSkill & { priority: 'high' | 'medium' | 'low' }

export type GapAnalysis = {
  current_title_id: number
  target_title_id: number
  readiness_score: number
  level_source: 'employee_profile' | 'current_title_market_proxy'
  gap: {
    matched: GapSkill[]
    missing: MissingSkill[]
    to_improve: GapSkill[]
    evidence_postings: number
    low_evidence: boolean
  }
  radar: GapSkill[]
}

export type PlanAction = {
  skill_id: number
  type: 'course' | 'project' | 'mentoring' | 'shadowing' | 'certification' | 'reading'
  title_ar: string
  effort_hours: number
  success_metric_ar: string
}

export type DevelopmentPlan = {
  current_title_id: number
  target_title_id: number
  readiness_score: number
  low_evidence: boolean
  phases: { phase: '30' | '60' | '90'; goal_ar: string; actions: PlanAction[] }[]
}

export function getTitles(): Promise<JobTitle[]> {
  return apiGet<JobTitle[]>('/api/career/titles')
}

export function getGapAnalysis(currentTitleId: number, targetTitleId: number): Promise<GapAnalysis> {
  const query = new URLSearchParams({
    current_title_id: String(currentTitleId),
    target_title_id: String(targetTitleId),
  })
  return apiGet<GapAnalysis>(`/api/career/gap-analysis?${query}`)
}

export function getPlan(currentTitleId: number, targetTitleId: number): Promise<DevelopmentPlan> {
  const query = new URLSearchParams({
    current_title_id: String(currentTitleId),
    target_title_id: String(targetTitleId),
  })
  return apiGet<DevelopmentPlan>(`/api/career/plan?${query}`)
}

// The career title that matches an employee profile's job_title; rejects with a 404 ApiError when none does.
export function matchTitle(jobTitle: string): Promise<JobTitle> {
  return apiGet<JobTitle>(`/api/career/titles/match?${new URLSearchParams({ job_title: jobTitle })}`)
}
