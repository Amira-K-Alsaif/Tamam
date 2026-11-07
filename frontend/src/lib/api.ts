// The only place the frontend talks to the backend. Feature code calls these
// functions instead of using fetch directly.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new ApiError(response.status, `GET ${path} failed`)
  }
  return (await response.json()) as T
}

export type HealthResponse = { status: 'ok' }

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>('/api/health')
}

// Onboarding (module 5). Shapes match backend/app/modules/onboarding/schemas.py.

export type EmployeeProfile = {
  id: string
  full_name: string
  department_id: string
  team: string
  job_title: string
  manager_id: string | null
  years_of_experience: number
  role: 'employee' | 'admin'
}

export type AccessStatus = 'active' | 'requested' | 'missing'

export type RoadmapItem = {
  kind: 'lesson' | 'access' | 'person'
  title: string
  reason: string
  week: number
  score: number | null
  access_item_id: string | null
  status: AccessStatus | null
  procedure_id: string | null
  approver_role: string | null
  expected_days: number | null
  employee_id: string | null
}

export type RoadmapWeek = { week: number; items: RoadmapItem[] }

export type Roadmap = { employee_id: string; weeks: RoadmapWeek[] }

export function getMe(): Promise<EmployeeProfile> {
  return apiGet<EmployeeProfile>('/api/onboarding/me')
}

export function getRoadmap(): Promise<Roadmap> {
  return apiGet<Roadmap>('/api/onboarding/roadmap')
}
