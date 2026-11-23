import { useEffect, useMemo, useState } from 'react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { PageHeader } from '../../components/PageHeader'
import { ProgressBar } from '../../components/ProgressBar'
import { StatusBadge, type Status } from '../../components/StatusBadge'
import { ApiError, getMe } from '../../lib/api'
import {
  getGapAnalysis,
  getPlan,
  getTitles,
  matchTitle,
  type DevelopmentPlan,
  type GapAnalysis,
  type GapSkill,
  type JobTitle,
  type PlanAction,
} from './api'
import { GapRadar } from './GapRadar'

const percent = new Intl.NumberFormat('ar-SA', { style: 'percent', maximumFractionDigits: 0 })
const PHASE_LABEL = { '30': 'أول ٣٠ يوم', '60': 'من ٣١ إلى ٦٠ يوم', '90': 'من ٦١ إلى ٩٠ يوم' } as const
const ACTION_LABEL: Record<PlanAction['type'], string> = {
  course: 'دورة',
  project: 'تطبيق عملي',
  mentoring: 'توجيه',
  shadowing: 'مرافقة',
  certification: 'شهادة',
  reading: 'قراءة',
}
const PRIORITY = { high: 'أولوية عالية', medium: 'أولوية متوسطة', low: 'أولوية منخفضة' } as const

// Where the current title came from: the employee's profile, or nothing to prefill.
type ProfileTitle =
  | { state: 'loading' }
  | { state: 'matched'; jobTitle: string }
  | { state: 'unmatched'; jobTitle: string }
  | { state: 'error' }

type Load<T> = { state: 'idle' } | { state: 'loading' } | { state: 'error' } | { state: 'done'; data: T }

const selectClass =
  'h-11 w-full rounded-full border border-line-strong bg-sunken px-4 text-ink disabled:opacity-50'

export default function CareerPage() {
  const [titles, setTitles] = useState<Load<JobTitle[]>>({ state: 'loading' })
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [targetId, setTargetId] = useState<number | null>(null)
  const [result, setResult] = useState<Load<GapAnalysis>>({ state: 'idle' })
  const [plan, setPlan] = useState<Load<DevelopmentPlan>>({ state: 'idle' })
  const [profileTitle, setProfileTitle] = useState<ProfileTitle>({ state: 'loading' })
  // Whose measured skill levels the gap uses, from the onboarding assessment and CV.
  const [employeeId, setEmployeeId] = useState<string | undefined>(undefined)

  useEffect(() => {
    getTitles()
      .then((data) => setTitles({ state: 'done', data }))
      .catch(() => setTitles({ state: 'error' }))
  }, [])

  useEffect(() => {
    if (titles.state !== 'done') return
    let cancelled = false
    getMe()
      .then(async (me) => {
        if (!cancelled) setEmployeeId(me.id)
        try {
          const match = await matchTitle(me.job_title)
          if (cancelled) return
          setCurrentId(match.id)
          setTargetId(match.next_title_id)
          setProfileTitle({ state: 'matched', jobTitle: me.job_title })
        } catch (err) {
          if (!(err instanceof ApiError && err.status === 404)) throw err
          if (!cancelled) setProfileTitle({ state: 'unmatched', jobTitle: me.job_title })
        }
      })
      .catch(() => {
        if (!cancelled) setProfileTitle({ state: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [titles.state])

  const byId = useMemo(
    () => new Map(titles.state === 'done' ? titles.data.map((t) => [t.id, t]) : []),
    [titles],
  )

  function analyze() {
    if (currentId === null || targetId === null) return
    setResult({ state: 'loading' })
    setPlan({ state: 'loading' })
    getGapAnalysis(currentId, targetId, employeeId)
      .then((data) => setResult({ state: 'done', data }))
      .catch(() => setResult({ state: 'error' }))
    getPlan(currentId, targetId, employeeId)
      .then((data) => setPlan({ state: 'done', data }))
      .catch(() => setPlan({ state: 'error' }))
  }

  return (
    <>
      <PageHeader
        title="مساري المهني"
        description="اختاري المنصب اللي تبين توصلين له، ونقارن مهاراتك بإعلانات الوظائف في السوق."
      />

      {titles.state === 'loading' && <p className="m-0 text-muted">نجهّز المسميات الوظيفية…</p>}
      {titles.state === 'error' && (
        <p role="alert" className="m-0 text-danger">
          ما قدرنا نجيب المسميات الوظيفية. تأكدي إن الخادم شغّال وحدّثي الصفحة.
        </p>
      )}

      {titles.state === 'done' && (
        <Card>
          <ProfileTitleNote profileTitle={profileTitle} />
          <div className="grid items-end gap-4 sm:grid-cols-3">
            <div className="flex flex-col gap-2 text-sm text-muted">
              منصبك الحالي
              <span className="flex h-11 items-center rounded-full border border-line bg-sunken px-4 text-base text-ink">
                {currentId === null ? '—' : (byId.get(currentId)?.name_ar ?? '—')}
              </span>
            </div>
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

      {result.state === 'done' && (
        <>
          <GapResult result={result.data} titles={byId} />
          <PlanCard plan={plan} />
        </>
      )}
    </>
  )
}

function ProfileTitleNote({ profileTitle }: { profileTitle: ProfileTitle }) {
  if (profileTitle.state === 'loading') return null
  const text =
    profileTitle.state === 'matched'
      ? null
      : profileTitle.state === 'unmatched'
        ? `منصبك في ملفك «${profileTitle.jobTitle}» ما عندنا له إعلانات وظائف للحين، فما نقدر نقارنه بالسوق.`
        : 'ما قدرنا نقرأ ملفك. حدّثي الصفحة وحاولي مرة ثانية.'
  return text && <p className="m-0 text-sm text-warning">{text}</p>
}

function GapResult({ result, titles }: { result: GapAnalysis; titles: Map<number, JobTitle> }) {
  const target = titles.get(result.target_title_id)
  const { matched, to_improve, missing, evidence_postings, low_evidence } = result.gap
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
              ? 'مستواك مأخوذ من تقييمك الأولي وسيرتك الذاتية، والمهارات اللي ما قسناها مقدّرة من السوق.'
              : 'قدّرنا مستواك من المهارات المعتادة لمنصبك الحالي في السوق. خلّصي التقييم الأولي في مساري التأهيلي عشان نقيس مستواك الحقيقي.'}
          </p>
          {target?.esco_occupation_uri && (
            <p className="m-0 mt-2 text-xs text-faint">
              المنصب في تصنيف{' '}
              <a href={target.esco_occupation_uri} target="_blank" rel="noreferrer" className="text-blue-soft underline">
                ESCO
              </a>{' '}
              (Skills/competences and occupations from ESCO, European Commission)
            </p>
          )}
          {low_evidence && (
            <p role="note" className="m-0 mt-2 text-sm text-warning">
              النتيجة تقريبية: عدد الإعلانات لهذا المنصب قليل، فالمهارات المطلوبة ممكن تكون ناقصة.
            </p>
          )}
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

function PlanCard({ plan }: { plan: Load<DevelopmentPlan> }) {
  return (
    <Card title="خطة التطوير">
      {plan.state === 'loading' && <p className="m-0 text-muted">نجهّز خطتك…</p>}
      {plan.state === 'error' && (
        <p role="alert" className="m-0 text-danger">
          ما قدرنا نجهّز الخطة. جرّبي التحليل مرة ثانية.
        </p>
      )}
      {plan.state === 'done' && plan.data.phases.length === 0 && (
        <p className="m-0 text-muted">عندك كل المهارات اللي يطلبها السوق لهذا المنصب، ما تحتاجين خطة 🎉</p>
      )}
      {plan.state === 'done' && plan.data.phases.length > 0 && (
        <ol className="m-0 flex list-none flex-col gap-6 p-0">
          {plan.data.phases.map((phase) => (
            <li key={phase.phase} className="flex flex-col gap-3">
              <div className="flex flex-col">
                <span className="text-sm text-mint">{PHASE_LABEL[phase.phase]}</span>
                <span className="font-display">{phase.goal_ar}</span>
              </div>
              <ul className="m-0 flex list-none flex-col gap-3 p-0">
                {phase.actions.map((action) => (
                  <li key={`${action.skill_id}-${action.type}`} className="flex items-start gap-3">
                    <StatusBadge status="in-progress" label={ACTION_LABEL[action.type]} />
                    <span className="flex flex-col">
                      <span>{action.title_ar}</span>
                      <span className="text-xs text-faint">
                        {action.effort_hours} ساعة · {action.success_metric_ar}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
