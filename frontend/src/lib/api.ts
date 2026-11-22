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
  topic: string | null
  document_id: string | null
}

export type RoadmapWeek = { week: number; items: RoadmapItem[] }

export type Roadmap = { employee_id: string; weeks: RoadmapWeek[] }

// What /api/onboarding/me returns: the profile plus the manager's name (null only for the CEO).
export type CurrentEmployee = EmployeeProfile & { manager_name: string | null }

// Demo only, until auth exists: view the onboarding pages as one of getDemoEmployees().
function asEmployee(employeeId?: string): string {
  return employeeId ? `?employee_id=${encodeURIComponent(employeeId)}` : ''
}

export function getMe(employeeId?: string): Promise<CurrentEmployee> {
  return apiGet<CurrentEmployee>(`/api/onboarding/me${asEmployee(employeeId)}`)
}

export function getRoadmap(employeeId?: string): Promise<Roadmap> {
  return apiGet<Roadmap>(`/api/onboarding/roadmap${asEmployee(employeeId)}`)
}

export type Badge = { id: string; title: string; description: string; earned: boolean }

export type Progress = {
  employee_id: string
  access_active: number
  access_total: number
  topics_passed: number
  topics_total: number
  percent: number
  badges: Badge[]
}

export type TeamMember = { employee: EmployeeProfile; progress: Progress; next_step: string | null }

export function getProgress(employeeId?: string): Promise<Progress> {
  return apiGet<Progress>(`/api/onboarding/progress${asEmployee(employeeId)}`)
}

export function getTeam(employeeId?: string): Promise<TeamMember[]> {
  return apiGet<TeamMember[]>(`/api/onboarding/team${asEmployee(employeeId)}`)
}

export function getDemoEmployees(): Promise<EmployeeProfile[]> {
  return apiGet<EmployeeProfile[]>('/api/onboarding/demo-employees')
}

export type QuizQuestion = {
  question: string
  options: string[]
  source: { document_id: string; document_title: string; section_title: string; quote: string }
}

export type Quiz = {
  topic: string
  document_id: string
  document_title: string
  questions: QuizQuestion[]
}

export type QuizResult = {
  topic: string
  score: number
  passed: boolean
  correct: boolean[]
  correct_options: number[]
}

export function getLessonQuiz(documentId: string): Promise<Quiz> {
  return apiGet<Quiz>(`/api/onboarding/lessons/${encodeURIComponent(documentId)}/quiz`)
}

export function answerLessonQuiz(
  documentId: string,
  answers: number[],
  employeeId?: string,
): Promise<QuizResult> {
  const path = `/api/onboarding/lessons/${encodeURIComponent(documentId)}/attempt`
  return apiPost<QuizResult>(`${path}${asEmployee(employeeId)}`, { answers })
}

// The starting assessment: a few questions per topic, generated from the policy documents.
export type AssessmentQuestion = QuizQuestion & { topic: string }

export type Assessment = { questions: AssessmentQuestion[] }

export type AssessmentOutcome = {
  scores: { topic: string; score: number; passed: boolean }[]
  correct: boolean[]
  correct_options: number[]
}

export function getAssessment(): Promise<Assessment> {
  return apiGet<Assessment>('/api/onboarding/assessment')
}

export function answerAssessment(answers: number[], employeeId?: string): Promise<AssessmentOutcome> {
  return apiPost<AssessmentOutcome>(`/api/onboarding/assessment/attempt${asEmployee(employeeId)}`, { answers })
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new ApiError(response.status, `POST ${path} failed`)
  }
  return (await response.json()) as T
}

// Chat (module 1). Shapes match backend/app/modules/chat/schemas.py.

export type Source = {
  document_id: string
  document_title: string
  // null for documents without pages, such as Markdown
  page: number | null
  section_title: string
  quote: string
}

export type AskResponse = {
  answer: string
  found: boolean
  sources: Source[]
}

export function askQuestion(question: string): Promise<AskResponse> {
  return apiPost<AskResponse>('/api/chat/ask', { question })
}
