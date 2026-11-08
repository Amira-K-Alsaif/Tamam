import { useEffect, useMemo, useState } from 'react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { PageHeader } from '../../components/PageHeader'
import { ProgressBar } from '../../components/ProgressBar'
import { StatusBadge, type Status } from '../../components/StatusBadge'
import { getGapAnalysis, getTitles, type GapAnalysis, type GapSkill, type JobTitle } from './api'
import { GapRadar } from './GapRadar'

const percent = new Intl.NumberFormat('ar-SA', { style: 'percent', maximumFractionDigits: 0 })
const PRIORITY = { high: 'أولوية عالية', medium: 'أولوية متوسطة', low: 'أولوية منخفضة' } as const

type Load<T> = { state: 'idle' } | { state: 'loading' } | { state: 'error' } | { state: 'done'; data: T }

const selectClass =
  'h-11 w-full rounded-full border border-line-strong bg-sunken px-4 text-ink disabled:opacity-50'

export default function CareerPage() {
  const [titles, setTitles] = useState<Load<JobTitle[]>>({ state: 'loading' })
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [targetId, setTargetId] = useState<number | null>(null)
  const [result, setResult] = useState<Load<GapAnalysis>>({ state: 'idle' })

  useEffect(() => {
    getTitles()
      .then((data) => setTitles({ state: 'done', data }))
      .catch(() => setTitles({ state: 'error' }))
  }, [])

  const byId = useMemo(
    () => new Map(titles.state === 'done' ? titles.data.map((t) => [t.id, t]) : []),
    [titles],
  )

  function chooseCurrent(id: number) {
    setCurrentId(id)
    setTargetId(byId.get(id)?.next_title_id ?? null)
    setResult({ state: 'idle' })
  }

  function analyze() {
    if (currentId === null || targetId === null) return
    setResult({ state: 'loading' })
    getGapAnalysis(currentId, targetId)
      .then((data) => setResult({ state: 'done', data }))
      .catch(() => setResult({ state: 'error' }))
  }

  return (
    <>
      <PageHeader
        title="مساري المهني"
        description="اختاري منصبك الحالي والمنصب اللي تبين توصلين له، ونقارنك بإعلانات الوظائف في السوق."
      />

      {titles.state === 'loading' && <p className="m-0 text-muted">نجهّز المسميات الوظيفية…</p>}
      {titles.state === 'error' && (
        <p role="alert" className="m-0 text-danger">
          ما قدرنا نجيب المسميات الوظيفية. تأكدي إن الخادم شغّال وحدّثي الصفحة.
        </p>
      )}

      {titles.state === 'done' && (
        <Card>
          <div className="grid items-end gap-4 sm:grid-cols-3">
            <label className="flex flex-col gap-2 text-sm text-muted">
              المنصب الحالي
              <select
                className={selectClass}
                value={currentId ?? ''}
                onChange={(e) => chooseCurrent(Number(e.target.value))}
              >
                <option value="" disabled>
                  اختاري…
                </option>
                {titles.data.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name_ar}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm text-muted">
              المنصب المستهدف
              <select
                className={selectClass}
                value={targetId ?? ''}
                onChange={(e) => {
                  setTargetId(Number(e.target.value))
                  setResult({ state: 'idle' })
                }}
              >
                <option value="" disabled>
                  اختاري…
                </option>
                {titles.data
                  .filter((t) => t.id !== currentId)
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name_ar} ({t.postings_count} إعلان)
                    </option>
                  ))}
              </select>
            </label>
            <Button
              onClick={analyze}
              disabled={currentId === null || targetId === null || result.state === 'loading'}
            >
              {result.state === 'loading' ? 'نحلّل…' : 'حلّلي الفجوة'}
            </Button>
          </div>
        </Card>
      )}

      {result.state === 'error' && (
        <p role="alert" className="m-0 text-danger">
          صار خطأ في التحليل. جرّبي مرة ثانية بعد شوي.
        </p>
      )}

      {result.state === 'done' && <GapResult result={result.data} titles={byId} />}
    </>
  )
}

function GapResult({ result, titles }: { result: GapAnalysis; titles: Map<number, JobTitle> }) {
  const target = titles.get(result.target_title_id)
  const { matched, to_improve, missing, evidence_postings } = result.gap
  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="جاهزيتك للمنصب">
          <ProgressBar label={target?.name_ar ?? ''} value={result.readiness_score} />
        </Card>
        <Card className="md:col-span-2">
          <p className="m-0 text-muted">
            مبني على {evidence_postings} إعلان وظيفي لمنصب «{target?.name_ar}».{' '}
            {result.level_source === 'employee_profile'
              ? 'مستواك مأخوذ من ملف مهاراتك.'
              : 'قدّرنا مستواك من المهارات المعتادة لمنصبك الحالي في السوق، لين يجهز ملف مهاراتك.'}
          </p>
        </Card>
      </div>

      <Card title="رادار الفجوة">
        {result.radar.length >= 3 ? (
          <GapRadar skills={result.radar} />
        ) : (
          <p className="m-0 text-muted">البيانات قليلة لهذا المنصب، نحتاج ٣ مهارات على الأقل للرسم.</p>
        )}
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <SkillList
          title="مهارات ناقصة"
          status="missing"
          skills={missing.map((s) => [s, `${PRIORITY[s.priority]} · يطلبها ${percent.format(s.market_frequency)} من الإعلانات`])}
        />
        <SkillList
          title="مهارات تحتاج تطوير"
          status="in-progress"
          skills={to_improve.map((s) => [s, `مستواك ${s.employee_level} من ${s.expected_level} المطلوبة`])}
        />
        <SkillList
          title="مهارات عندك"
          status="done"
          skills={matched.map((s) => [s, `يطلبها ${percent.format(s.market_frequency)} من الإعلانات`])}
        />
      </div>
    </>
  )
}

function SkillList({ title, status, skills }: { title: string; status: Status; skills: [GapSkill, string][] }) {
  return (
    <Card title={title} action={<StatusBadge status={status} label={String(skills.length)} />}>
      {skills.length === 0 ? (
        <p className="m-0 text-sm text-faint">ولا مهارة</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {skills.map(([skill, note]) => (
            <li key={skill.skill_id} className="flex flex-col">
              <span>{skill.label_ar}</span>
              <span className="text-xs text-faint">{note}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
