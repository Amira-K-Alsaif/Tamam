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
