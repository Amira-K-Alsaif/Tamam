import { AlertTriangle, ClipboardCheck, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type Evidence = {
  document_id: string
  document_title: string
  section_title: string
  chunk_id: string
  quote: string
}
type Conflict = { status: string; reason: string; unit: string; values: number[]; sources: Evidence[] }
type QualityIssue = { type: string; chunk_id?: string; document_id?: string; original_id?: string }
type Quality = { documents_count: number; chunks_count: number; issues_count: number; issues: QualityIssue[]; truncated: boolean }
type PolicyAlert = { id: number; document_id: string; document_title: string; event_type: string; changed_at: string }
type ReviewResults = [
  PromiseSettledResult<{ candidates: Conflict[] }>,
  PromiseSettledResult<Quality>,
  PromiseSettledResult<{ alerts: PolicyAlert[] }>,
]

const EVENT_NAME: Record<string, string> = { created: 'أُضيفت', updated: 'حُدّثت', deleted: 'حُذفت' }
const ISSUE_NAME: Record<string, string> = {
  duplicate_chunk: 'مقطع مكرر', orphan_chunk: 'مقطع دون وثيقة',
  empty_chunk: 'مقطع فارغ', missing_section_title: 'عنوان قسم مفقود',
  missing_document_title: 'اسم وثيقة مفقود',
}
const UNIT_NAME: Record<string, string> = { day: 'يوم', hour: 'ساعة', month: 'شهر', minute: 'دقيقة' }

async function readAdmin<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/knowledge/${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error(`تعذر تحميل ${path} (${response.status})`)
  return (await response.json()) as T
}

/** An admin-only, non-destructive review view: findings are not verified contradictions. */
export function KnowledgeReviewPanel({ token }: { token: string }) {
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [quality, setQuality] = useState<Quality | null>(null)
  const [alerts, setAlerts] = useState<PolicyAlert[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const loadReview = useCallback((): Promise<ReviewResults> => Promise.allSettled([
    readAdmin<{ candidates: Conflict[] }>('conflicts', token),
    readAdmin<Quality>('quality', token),
    readAdmin<{ alerts: PolicyAlert[] }>('alerts', token),
  ]), [token])

  const applyResults = useCallback((results: ReviewResults) => {
    const failures: string[] = []
    if (results[0].status === 'fulfilled') setConflicts(results[0].value.candidates)
    else failures.push('تعذر فحص تعارض السياسات')
    if (results[1].status === 'fulfilled') setQuality(results[1].value)
    else failures.push('تعذر تدقيق جودة البيانات')
    if (results[2].status === 'fulfilled') setAlerts(results[2].value.alerts)
    else failures.push('تعذر تحميل التنبيهات؛ تأكدي من تطبيق migration')
    setErrors(failures)
    setLoading(false)
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    applyResults(await loadReview())
  }, [applyResults, loadReview])

  useEffect(() => {
    // Apply asynchronous fetch results only while this panel is mounted.
    let active = true
    void loadReview().then((results) => {
      if (active) applyResults(results)
    })
    return () => { active = false }
  }, [loadReview, applyResults])

  return (
    <section aria-label="مراجعة المعرفة" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="m-0 font-display text-xl font-semibold">مراجعة جودة المعرفة</h2>
          <p className="m-0 text-sm text-faint">النتائج مؤشرات آلية تحتاج اعتماد المشرف، ولا تعدّل البيانات تلقائيًا.</p>
        </div>
        <Button variant="secondary" disabled={loading} onClick={() => void refresh()}>
          <RefreshCw aria-hidden className="size-4" /> {loading ? 'جارٍ الفحص…' : 'تحديث الفحص'}
        </Button>
      </div>
      {errors.length > 0 && <p role="alert" className="m-0 text-sm text-danger">{errors.join(' · ')}</p>}
      <Card title={`تعارضات محتملة (${conflicts.length})`}>
        {conflicts.length === 0 ? (
          <p className="m-0 text-sm text-muted">لم يُرصد اختلاف رقمي واضح في النصوص المتشابهة. هذا لا يثبت خلو الوثائق من التعارضات.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-4 p-0">
            {conflicts.map((finding, index) => (
              <li key={`${finding.sources.map((s) => s.chunk_id).join('-')}-${index}`} className="rounded-xl border border-line p-4">
                <p className="m-0 mb-2 flex items-center gap-2 text-sm text-warning">
                  <AlertTriangle aria-hidden className="size-4" /> للمراجعة: اختلاف قيم ({finding.values.join(' / ')} {UNIT_NAME[finding.unit] ?? finding.unit})
                </p>
                {finding.sources.map((source) => (
                  <blockquote key={`${source.document_id}:${source.chunk_id}`} className="my-2 border-s-2 border-line-strong ps-3">
                    <strong className="text-sm">{source.document_title} — {source.section_title}</strong>
                    <p className="m-0 text-sm text-soft">«{source.quote}»</p>
                    <span className="text-xs text-faint">{source.document_id} · {source.chunk_id}</span>
                  </blockquote>
                ))}
              </li>
            ))}
          </ul>
        )}
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="جودة البيانات">
          {quality ? (
            <>
              <p className="m-0 flex items-center gap-2 text-sm text-soft">
                <ClipboardCheck aria-hidden className="size-4 text-mint" />
                {quality.documents_count} وثيقة · {quality.chunks_count} مقطع · {quality.issues_count} ملاحظة
              </p>
              {quality.issues.length ? (
                <ul className="m-0 list-inside list-disc text-sm text-muted">
                  {quality.issues.map((issue, index) => <li key={`${issue.chunk_id ?? issue.document_id}-${index}`}>{ISSUE_NAME[issue.type] ?? issue.type}: {issue.chunk_id ?? issue.document_id}</li>)}
                </ul>
              ) : <p className="m-0 text-sm text-muted">لا توجد ملاحظات في الفحوصات الحالية.</p>}
              {quality.truncated && <p className="m-0 text-xs text-warning">عُرض جزء من الملاحظات فقط.</p>}
            </>
          ) : <p className="m-0 text-sm text-muted">بيانات الفحص غير متاحة.</p>}
        </Card>
        <Card title="تنبيهات تغيّر السياسات">
          {alerts.length ? (
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {alerts.map((alert) => (
                <li key={alert.id} className="rounded-lg border border-line p-3 text-sm">
                  <strong>{EVENT_NAME[alert.event_type] ?? alert.event_type} سياسة: {alert.document_title}</strong>
                  <p className="m-0 text-xs text-faint">{new Date(alert.changed_at).toLocaleString('ar-SA')}</p>
                </li>
              ))}
            </ul>
          ) : <p className="m-0 text-sm text-muted">لا توجد أحداث تغيّر مسجلة حتى الآن.</p>}
        </Card>
      </div>
    </section>
  )
}
