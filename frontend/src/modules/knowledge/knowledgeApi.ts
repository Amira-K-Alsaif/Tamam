/** Knowledge administration API. Only public Supabase keys may reach the browser. */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string | undefined
const SUPABASE_PUBLIC_KEY = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ??
  import.meta.env.VITE_SUPABASE_ANON_KEY) as string | undefined

const ROOT = '/api/knowledge/documents'
export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024
export type DocumentKind = 'policy' | 'procedure' | 'form' | 'faq'

export type KnowledgeDocument = {
  id: string
  title: string
  kind: DocumentKind
  department: string
  status: string
  updated_at: string | null
}

async function readJson<T>(response: Response): Promise<T> {
  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : undefined
    throw new Error(typeof detail === 'string' ? detail : `تعذر إكمال الطلب (HTTP ${response.status})`)
  }
  return data as T
}

async function adminRequest<T>(
  path: string,
  token: string,
  method: 'GET' | 'POST' | 'DELETE',
  body?: FormData,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    body,
  })
  return readJson<T>(response)
}

/** Sign in with a Supabase user. The backend independently checks app_metadata.role. */
export async function signInKnowledgeAdmin(email: string, password: string): Promise<string> {
  if (!SUPABASE_URL || !SUPABASE_PUBLIC_KEY) {
    throw new Error('أضيفي VITE_SUPABASE_URL وVITE_SUPABASE_PUBLISHABLE_KEY إلى frontend/.env.local')
  }

  const response = await fetch(`${SUPABASE_URL.replace(/\/$/, '')}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: { apikey: SUPABASE_PUBLIC_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error('تعذر تسجيل الدخول. تحققي من البريد وكلمة المرور.')

  const result = (await response.json()) as { access_token?: string }
  if (!result.access_token) throw new Error('لم يرجع مزود الدخول رمز وصول صالحًا')
  return result.access_token
}

export function listKnowledgeDocuments(token: string): Promise<{ documents: KnowledgeDocument[] }> {
  return adminRequest(ROOT, token, 'GET')
}

export function uploadKnowledgeDocument(
  token: string,
  file: File,
  title: string,
  kind: DocumentKind,
  department: string,
): Promise<{ id: string; title: string; status: string; chunks_count: number }> {
  if (!file.size || file.size > MAX_UPLOAD_BYTES) {
    throw new Error('حجم الملف يجب أن يكون أكثر من صفر ولا يتجاوز 20MB')
  }
  if (!/\.(pdf|docx|md|txt)$/i.test(file.name)) {
    throw new Error('نوع الملف غير مدعوم')
  }

  const form = new FormData()
  form.append('file', file)
  form.append('title', title.trim())
  form.append('kind', kind)
  form.append('department', department.trim())
  // Do not set Content-Type: the browser supplies the multipart boundary.
  return adminRequest(ROOT, token, 'POST', form)
}

export function deleteKnowledgeDocument(token: string, documentId: string): Promise<{ status: string }> {
  if (!/^upload-[0-9a-f]{32}$/.test(documentId)) {
    throw new Error('لا يمكن حذف الوثائق الأساسية')
  }
  return adminRequest(`${ROOT}/${encodeURIComponent(documentId)}`, token, 'DELETE')
}
