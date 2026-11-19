import { apiGet } from '../../lib/api'

// Shapes match backend/app/modules/org_map/schemas.py.

export type Gender = 'f' | 'm'
export type Relation = 'self' | 'manager' | 'mentor'

export type PersonSummary = {
  id: string
  full_name: string
  gender: Gender
  job_title: string
  department_id: string
  team: string
  is_department_head: boolean
  relation: Relation | null
}

export type PersonDetail = PersonSummary & {
  department_name: string
  email: string
  office: string
  contact_topics: string[]
  procedures: { id: string; title: string }[]
}

export type DepartmentSummary = {
  id: string
  name: string
  head: PersonSummary
  headcount: number
  is_mine: boolean
}

export type OrgOverview = {
  company_name: string
  employee_count: number
  ceo: PersonSummary
  departments: DepartmentSummary[]
  my_department_id: string
  my_manager_id: string | null
}

export type DepartmentDetail = {
  id: string
  name: string
  headcount: number
  teams: { name: string; size: number }[]
  members: PersonSummary[]
}

export type SearchHit = { person: PersonSummary; department_name: string; matched_topic: string }

export type SearchResponse = { query: string; hits: SearchHit[] }

export function getOverview(): Promise<OrgOverview> {
  return apiGet<OrgOverview>('/api/org-map/overview')
}

export function getDepartment(id: string): Promise<DepartmentDetail> {
  return apiGet<DepartmentDetail>(`/api/org-map/departments/${encodeURIComponent(id)}`)
}

export function getPerson(id: string): Promise<PersonDetail> {
  return apiGet<PersonDetail>(`/api/org-map/people/${encodeURIComponent(id)}`)
}

export function searchPeople(query: string): Promise<SearchResponse> {
  return apiGet<SearchResponse>(`/api/org-map/search?q=${encodeURIComponent(query)}`)
}
