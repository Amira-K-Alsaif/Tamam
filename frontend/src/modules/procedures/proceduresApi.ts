// Procedures (module 3). Shapes match backend/app/modules/procedures/schemas.py.
import { apiGet } from '../../lib/api'

export type ProcedureStep = {
  order: number
  title: string
  detail: string
}

export type ProcedureSource = {
  document_id: string
  document_title: string
  page: number | null
  section_title: string | null
  quote: string
}

export type Procedure = {
  // "proc-<document id>": the procedure_id other modules reference.
  id: string
  title: string
  department: string
  summary: string
  owner: string | null
  duration_text: string | null
  requirements: string[]
  forms: string[]
  steps: ProcedureStep[]
  source: ProcedureSource
}

export type ProcedureFilter = {
  query?: string
  department?: string | null
}

export function listProcedures({ query, department }: ProcedureFilter = {}): Promise<Procedure[]> {
  const params = new URLSearchParams()
  if (query?.trim()) params.set('q', query.trim())
  if (department) params.set('department', department)
  const search = params.toString()
  return apiGet<Procedure[]>(`/api/procedures${search ? `?${search}` : ''}`)
}

export function getProcedure(id: string): Promise<Procedure> {
  return apiGet<Procedure>(`/api/procedures/${encodeURIComponent(id)}`)
}
