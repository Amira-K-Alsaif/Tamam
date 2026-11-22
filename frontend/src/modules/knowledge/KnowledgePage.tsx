import { FilePlus2, FileText, LogOut, RefreshCw, Trash2 } from 'lucide-react'
import { KnowledgeReviewPanel } from './KnowledgeReviewPanel'
import { useState, type FormEvent } from 'react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { PageHeader } from '../../components/PageHeader'
import {
  deleteKnowledgeDocument,
  listKnowledgeDocuments,
  signInKnowledgeAdmin,
  uploadKnowledgeDocument,
  type DocumentKind,
  type KnowledgeDocument,
} from './knowledgeApi'

const FIELD = 'w-full rounded-xl border border-line-strong bg-sunken px-4 py-2 text-ink'
const CAN_DELETE = /^upload-[0-9a-f]{32}$/
const KIND_NAMES: Record<DocumentKind, string> = {
  policy: 'سياسة',
  procedure: 'إجراء',
  form: 'نموذج',
  faq: 'أسئلة شائعة',
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'حدث خطأ غير متوقع'
}

export default function KnowledgePage() {
  const [token, setToken] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('')
  const [kind, setKind] = useState<DocumentKind>('policy')
  const [file, setFile] = useState<File | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refresh(accessToken: string) {
    const result = await listKnowledgeDocuments(accessToken)
    setDocuments(result.documents)
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const accessToken = await signInKnowledgeAdmin(email.trim(), password)
      // A valid login is not enough: only a backend-authorized admin can list documents.
      await refresh(accessToken)
      setToken(accessToken)
      setPassword('')
      setNotice('تم تسجيل الدخول بصلاحية المشرف')
    } catch (err) {
      setError(getMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleRefresh() {
    if (!token) return
    setBusy(true)
    setError('')
    try {
      await refresh(token)
      setNotice('تم تحديث قائمة الوثائق')
    } catch (err) {
      setError(getMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token || !file) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const result = await uploadKnowledgeDocument(token, file, title, kind, department)
      await refresh(token)
      setNotice(`تمت معالجة «${result.title}» وإعداد ${result.chunks_count} مقطع للبحث`)
      setTitle('')
      setDepartment('')
      setFile(null)
      setFileInputKey((value) => value + 1)
    } catch (err) {
      setError(getMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(document: KnowledgeDocument) {
    if (!token || !CAN_DELETE.test(document.id)) return
    if (!window.confirm(`هل تريدين حذف الوثيقة «${document.title}» نهائيًا؟`)) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await deleteKnowledgeDocument(token, document.id)
      await refresh(token)
      setNotice(`تم حذف الوثيقة «${document.title}»`)
    } catch (err) {
      setError(getMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function logout() {
    setToken(null)
    setDocuments([])
    setPassword('')
    setError('')
    setNotice('تم إنهاء جلسة الإدارة')
  }

  return (
    <>
      <PageHeader
        title="مصنع المعرفة"
        description="إدارة وثائق الشركة وتحويلها إلى معرفة موثوقة قابلة للبحث."
        actions={token ? (
          <div className="flex gap-2">
            <Button variant="secondary" disabled={busy} onClick={() => void handleRefresh()}>
              <RefreshCw aria-hidden className="size-4" /> تحديث
            </Button>
            <Button variant="secondary" onClick={logout}>
              <LogOut aria-hidden className="size-4" /> خروج
            </Button>
          </div>
        ) : undefined}
      />

      {error && <p role="alert" className="m-0 rounded-xl border border-danger/40 p-3 text-danger">{error}</p>}
      {notice && <p role="status" className="m-0 rounded-xl border border-mint/30 p-3 text-mint">{notice}</p>}

      {!token ? (
        <Card title="دخول المشرف" className="max-w-xl">
          <p className="m-0 text-sm text-muted">
            إدارة الوثائق متاحة للمشرفين فقط. يُتحقق من الصلاحية في الخادم، وليس من واجهة المستخدم.
          </p>
          <form onSubmit={(event) => void handleLogin(event)} className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm" htmlFor="admin-email">
              البريد الإلكتروني
              <input id="admin-email" type="email" autoComplete="username" required value={email}
                onChange={(event) => setEmail(event.target.value)} className={FIELD} />
            </label>
            <label className="flex flex-col gap-1 text-sm" htmlFor="admin-password">
              كلمة المرور
              <input id="admin-password" type="password" autoComplete="current-password" required
                value={password} onChange={(event) => setPassword(event.target.value)} className={FIELD} />
            </label>
            <Button type="submit" disabled={busy}>{busy ? 'جارٍ التحقق…' : 'دخول المشرف'}</Button>
          </form>
        </Card>
      ) : (
        <>
          <Card title="رفع وثيقة جديدة">
            <form onSubmit={(event) => void handleUpload(event)} className="grid gap-4 sm:grid-cols-2">
              <label className="flex flex-col gap-1 text-sm" htmlFor="document-title">
                اسم الوثيقة
                <input id="document-title" required maxLength={180} value={title}
                  onChange={(event) => setTitle(event.target.value)} className={FIELD} />
              </label>
              <label className="flex flex-col gap-1 text-sm" htmlFor="document-department">
                القسم
                <input id="document-department" required maxLength={120} value={department}
                  onChange={(event) => setDepartment(event.target.value)} className={FIELD} />
              </label>
              <label className="flex flex-col gap-1 text-sm" htmlFor="document-kind">
                نوع الوثيقة
                <select id="document-kind" value={kind} onChange={(event) => setKind(event.target.value as DocumentKind)} className={FIELD}>
                  {Object.entries(KIND_NAMES).map(([key, value]) => <option key={key} value={key}>{value}</option>)}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-sm" htmlFor="document-file">
                الملف (PDF، Word، MD، TXT — حتى 20MB)
                <input key={fileInputKey} id="document-file" type="file" required
                  accept=".pdf,.docx,.md,.txt" className={FIELD}
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </label>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={busy || !file || !title.trim() || !department.trim()}>
                  <FilePlus2 aria-hidden className="size-4" /> {busy ? 'جارٍ المعالجة…' : 'رفع ومعالجة الوثيقة'}
                </Button>
              </div>
            </form>
          </Card>

          <Card title={`الوثائق (${documents.length})`}>
            {documents.length === 0 ? (
              <p className="m-0 text-muted">لا توجد وثائق مسجّلة حاليًا.</p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-3 p-0">
                {documents.map((document) => (
                  <li key={document.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line p-4">
                    <div className="flex min-w-0 items-start gap-3">
                      <FileText aria-hidden className="mt-1 size-5 shrink-0 text-mint" />
                      <div className="min-w-0">
                        <strong className="block break-words">{document.title}</strong>
                        <p className="m-0 text-sm text-faint">
                          {KIND_NAMES[document.kind] ?? document.kind} · {document.department} · {document.status === 'ready' ? 'جاهزة' : document.status === 'processing' ? 'قيد المعالجة' : document.status}
                        </p>
                      </div>
                    </div>
                    {CAN_DELETE.test(document.id) ? (
                      <Button variant="secondary" disabled={busy} onClick={() => void handleDelete(document)}>
                        <Trash2 aria-hidden className="size-4" /> حذف
                      </Button>
                    ) : (
                      <span className="text-xs text-faint">وثيقة أساسية</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <KnowledgeReviewPanel token={token} />
        </>
      )}
    </>
  )
}
