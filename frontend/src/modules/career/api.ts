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
  esco_occupation_uri: string | null
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

// Every action is one the employee does alone.
export type PlanAction = {
  skill_id: number
  type: 'self_study' | 'practice' | 'project' | 'certification'
  title_ar: string
  steps_ar: string[]
  effort_hours: number
  success_metric_ar: string
}

export type DevelopmentPlan = {
  current_title_id: number
  target_title_id: number
  readiness_score: number
  low_evidence: boolean
  phases: { phase: '30' | '60' | '90'; goal_ar: string; actions: PlanAction[] }[]
  // Who wrote the actions: the model for this gap, or the rule templates.
  written_by: 'ai' | 'rules'
}

export function getTitles(): Promise<JobTitle[]> {
  return apiGet<JobTitle[]>('/api/career/titles')
}

// With employeeId, the employee's measured skill levels replace the market estimate.
export function getGapAnalysis(currentTitleId: number, targetTitleId: number, employeeId?: string): Promise<GapAnalysis> {
  const query = new URLSearchParams({
    current_title_id: String(currentTitleId),
    target_title_id: String(targetTitleId),
    ...(employeeId ? { employee_id: employeeId } : {}),
  })
  return apiGet<GapAnalysis>(`/api/career/gap-analysis?${query}`)
}

// With employeeId, the employee's measured skill levels replace the market estimate.
export function getPlan(currentTitleId: number, targetTitleId: number, employeeId?: string): Promise<DevelopmentPlan> {
  const query = new URLSearchParams({
    current_title_id: String(currentTitleId),
    target_title_id: String(targetTitleId),
    ...(employeeId ? { employee_id: employeeId } : {}),
  })
  return apiGet<DevelopmentPlan>(`/api/career/plan?${query}`)
}

// The career title that matches an employee profile's job_title; rejects with a 404 ApiError when none does.
export function matchTitle(jobTitle: string): Promise<JobTitle> {
  return apiGet<JobTitle>(`/api/career/titles/match?${new URLSearchParams({ job_title: jobTitle })}`)
}
