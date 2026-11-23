import { useEffect, useState } from 'react'

import { Button, ButtonLink } from '../../components/Button'
import { Card } from '../../components/Card'
import { Diamond } from '../../components/Diamond'
import { PageHeader } from '../../components/PageHeader'
import { ProgressBar } from '../../components/ProgressBar'
import { StatusBadge } from '../../components/StatusBadge'
import type { Status } from '../../components/StatusBadge'
import { getDemoEmployees, getMe, getProgress, getRoadmap, getTeam } from '../../lib/api'
import type {
  AccessStatus,
  Badge,
  EmployeeProfile,
  Progress,
  Roadmap,
  RoadmapItem,
  TeamMember,
} from '../../lib/api'
import { moduleById } from '../modules'
import { LessonQuiz } from './LessonQuiz'
import { StartingAssessment } from './StartingAssessment'
import { taskCount, weekName } from './weeks'

const ACCESS_BADGES: Record<AccessStatus, { status: Status; label: string }> = {
  active: { status: 'done', label: 'مفعّلة' },
  requested: { status: 'in-progress', label: 'بانتظار الموافقة' },
  missing: { status: 'missing', label: 'ناقصة' },
}

const KIND_TONES = { access: 'teal', person: 'blue', lesson: 'mint', skill: 'mint' } as const

const SECTION_TITLES = {
  access: 'صلاحيات ناقصة',
  person: 'أشخاص تقابلهم',
  lesson: 'دروس عن الشركة',
  skill: 'مهارات تطوّرينها',
} as const

type PageData = {
  employeeId: string
  me: EmployeeProfile
  roadmap: Roadmap
  progress: Progress
  team: TeamMember[]
}

// Owned by team member 5. The new employee's roadmap, grouped by week; see docs/team.md.
export default function OnboardingPage() {
  const info = moduleById('onboarding')
  const [demoEmployees, setDemoEmployees] = useState<EmployeeProfile[]>([])
  const [chosenId, setChosenId] = useState<string | null>(null)
  const [data, setData] = useState<PageData | null>(null)
  const [failedId, setFailedId] = useState<string | null>(null)
  const [selectedWeek, setSelectedWeek] = useState(1)
  // Bumped after a quiz or the assessment is answered, so the roadmap, progress, and badges reload.
  const [reloadKey, setReloadKey] = useState(0)

  // Until auth exists, the page shows the first demo employee unless another is chosen.
  const employeeId = chosenId ?? demoEmployees[0]?.id ?? null

  useEffect(() => {
    let cancelled = false
    getDemoEmployees()
      .then((employees) => {
        if (!cancelled) setDemoEmployees(employees)
      })
      .catch(() => {
        if (!cancelled) setFailedId('demo')
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!employeeId) return
    let cancelled = false
    Promise.all([
      getMe(employeeId),
      getRoadmap(employeeId),
      getProgress(employeeId),
      getTeam(employeeId),
    ])
      .then(([me, roadmap, progress, team]) => {
        if (!cancelled) setData({ employeeId, me, roadmap, progress, team })
      })
      .catch(() => {
        if (!cancelled) setFailedId(employeeId)
      })
    return () => {
      cancelled = true
    }
  }, [employeeId, reloadKey])

  const switcher = (
    <DemoSwitcher
      employees={demoEmployees}
      value={employeeId}
      onChange={(id) => {
        setChosenId(id)
        setSelectedWeek(1)
      }}
    />
  )

  if (failedId && (failedId === 'demo' || failedId === employeeId)) {
    return (
      <>
        <PageHeader title={info.title} description={info.summary} />
        <Card>
          <p className="m-0 text-danger">ما قدرنا نجيب مسارك. تأكدي إن الخادم شغّال وحاولي مرة ثانية.</p>
        </Card>
      </>
    )
  }

  if (!data || data.employeeId !== employeeId) {
    return (
      <>
        <PageHeader title={info.title} description={info.summary} actions={switcher} />
        <p className="m-0 text-muted">جاري تجهيز المسار…</p>
      </>
    )
  }

  const { me, roadmap, progress, team } = data

  // Every employee starts with the assessment: the path is drawn from its result.
  if (!roadmap.assessed) {
    return (
      <>
        <PageHeader title={info.title} description={`أهلاً ${me.full_name} · ${me.job_title}.`} actions={switcher} />
        <StartingAssessment
          key={me.id}
          employeeId={me.id}
          onDone={() => {
            setSelectedWeek(1)
            setReloadKey((key) => key + 1)
          }}
        />
        {team.length > 0 && <TeamSection team={team} />}
      </>
    )
  }

  const allItems = roadmap.weeks.flatMap((week) => week.items)
  const week = roadmap.weeks.find((w) => w.week === selectedWeek) ?? roadmap.weeks[0]

  return (
    <>
      <PageHeader
        title={info.title}
        description={`أهلاً ${me.full_name} · ${me.job_title}. هذا كل اللي ناقصك، مرتّب بالأسابيع.`}
        actions={switcher}
      />
      {roadmap.drawn_by === 'ai' && (
        <p className="m-0 text-sm text-mint">رتّب تمّام دروسك ومهاراتك من نتيجة تقييمك الأولي.</p>
      )}

      <ProgressSummary items={allItems} progress={progress} />
      <BadgesSection badges={progress.badges} />
      {team.length > 0 && <TeamSection team={team} />}

      {roadmap.weeks.length === 0 ? (
        <Card>
          <div className="flex items-center gap-3">
            <Diamond />
            <strong>ما ينقصك شي. مسارك مكتمل.</strong>
          </div>
        </Card>
      ) : (
        <>
          <div role="tablist" aria-label="أسابيع المسار" className="flex flex-wrap gap-2">
            {roadmap.weeks.map((w) => {
              const selected = w.week === week.week
              return (
                <button
                  key={w.week}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  onClick={() => setSelectedWeek(w.week)}
                  className={`flex cursor-pointer items-center gap-2 rounded-full border px-4 py-1.5 font-body ${
                    selected ? 'border-mint bg-raised text-ink' : 'border-line bg-surface text-muted'
                  }`}
                >
                  {weekName(w.week)}
                  <span className="text-xs text-faint">{taskCount(w.items.length)}</span>
                </button>
              )
            })}
          </div>

          {(['access', 'person', 'lesson', 'skill'] as const).map((kind) => (
            <ItemsSection
              key={kind}
              title={SECTION_TITLES[kind]}
              items={week.items.filter((i) => i.kind === kind)}
              employeeId={me.id}
              onQuizAnswered={() => setReloadKey((key) => key + 1)}
            />
          ))}
        </>
      )}
    </>
  )
}

function DemoSwitcher({
  employees,
  value,
  onChange,
}: {
  employees: EmployeeProfile[]
  value: string | null
  onChange: (id: string) => void
}) {
  if (employees.length === 0) return null
  return (
    <label className="flex items-center gap-2 text-sm text-muted">
      <select
        aria-label="الموظف"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-full border border-line bg-surface px-3 py-1.5 font-body text-ink"
      >
        {employees.map((employee) => (
          <option key={employee.id} value={employee.id}>
            {employee.full_name} · {employee.job_title}
          </option>
        ))}
      </select>
    </label>
  )
}

function ProgressSummary({ items, progress }: { items: RoadmapItem[]; progress: Progress }) {
  const counts = [
    { label: 'صلاحيات ناقصة', value: items.filter((i) => i.kind === 'access').length },
    { label: 'أشخاص تقابلهم', value: items.filter((i) => i.kind === 'person').length },
    { label: 'دروس', value: items.filter((i) => i.kind === 'lesson').length },
    { label: 'مهارات تطوّرينها', value: items.filter((i) => i.kind === 'skill').length },
  ]
  return (
    <Card>
      <ProgressBar label="تقدّمك في المسار" value={progress.percent} />
      <p className="m-0 text-sm text-faint">
        {progress.access_active} من {progress.access_total} صلاحيات مفعّلة ·{' '}
        {progress.topics_passed} من {progress.topics_total} مواضيع ناجحة ·{' '}
        {progress.skills_ready} من {progress.skills_total} مهارات بالمستوى المطلوب
      </p>
      <div className="flex flex-wrap gap-4">
        {counts.map((count) => (
          <div
            key={count.label}
            className="flex min-w-40 flex-1 flex-col gap-1 rounded-2xl bg-sunken p-4"
          >
            <span className="font-display text-3xl font-extrabold">{count.value}</span>
            <span className="text-faint">{count.label}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function BadgesSection({ badges }: { badges: Badge[] }) {
  const earned = badges.filter((badge) => badge.earned).length
  return (
    <Card
      title="شاراتك"
      action={
        <span className="text-sm text-faint">
          {earned} من {badges.length}
        </span>
      }
    >
      <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
        {badges.map((badge) => (
          <li
            key={badge.id}
            className={`flex min-w-48 flex-1 items-start gap-3 rounded-2xl border p-4 ${
              badge.earned ? 'border-mint bg-raised' : 'border-line bg-sunken opacity-60'
            }`}
          >
            <span className="pt-2">
              <Diamond filled={badge.earned} />
            </span>
            <div className="flex flex-col">
              <strong>{badge.title}</strong>
              <span className="text-sm text-muted">{badge.description}</span>
              <span className={`text-xs ${badge.earned ? 'text-mint' : 'text-faint'}`}>
                {badge.earned ? 'حصلت عليها' : 'لسا'}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function TeamSection({ team }: { team: TeamMember[] }) {
  return (
    <Card title="فريقي" action={<span className="text-sm text-faint">الأقل تقدّماً أول</span>}>
      <ul className="m-0 flex list-none flex-col gap-5 p-0">
        {team.map(({ employee, progress, next_step }) => (
          <li key={employee.id} className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <strong>
                {employee.full_name} · <span className="font-normal text-muted">{employee.job_title}</span>
              </strong>
              <span className="text-sm text-faint">
                {progress.badges.filter((badge) => badge.earned).length} من {progress.badges.length}{' '}
                شارات
              </span>
            </div>
            <ProgressBar
              label={next_step ? `الخطوة الجاية: ${next_step}` : 'أكمل مساره'}
              value={progress.percent}
            />
          </li>
        ))}
      </ul>
    </Card>
  )
}

function ItemsSection({
  title,
  items,
  employeeId,
  onQuizAnswered,
}: {
  title: string
  items: RoadmapItem[]
  employeeId: string
  onQuizAnswered: () => void
}) {
  const [openQuiz, setOpenQuiz] = useState<string | null>(null)
  if (items.length === 0) return null
  return (
    <Card title={title}>
      <ul className="m-0 flex list-none flex-col gap-4 p-0">
        {items.map((item) => (
          <li key={`${item.kind}-${item.title}`} className="flex gap-3">
            <span className="pt-2.5">
              <Diamond tone={KIND_TONES[item.kind]} filled={false} />
            </span>
            <div className="flex flex-1 flex-col gap-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong>{item.title}</strong>
                {item.status && <StatusBadge {...ACCESS_BADGES[item.status]} />}
              </div>
              <span className="text-muted">{item.reason}</span>
              {item.kind === 'access' && <AccessDetails item={item} />}
              {item.kind === 'person' && item.employee_id && (
                <ButtonLink
                  variant="secondary"
                  className="h-9 self-start"
                  to={`/org-map?person=${encodeURIComponent(item.employee_id)}`}
                >
                  افتحي بطاقته في خريطة الشركة
                </ButtonLink>
              )}
              {item.kind === 'skill' && item.level !== null && item.expected_level !== null && (
                <ProgressBar
                  label={`مستواك ${item.level} من 4، والمطلوب ${item.expected_level}`}
                  value={(item.level / item.expected_level) * 100}
                />
              )}
              {item.kind === 'lesson' && item.score !== null && (
                <ProgressBar label="درجتك في التقييم" value={item.score} />
              )}
              {item.kind === 'lesson' && item.document_id && (
                openQuiz === item.document_id ? (
                  <LessonQuiz
                    documentId={item.document_id}
                    employeeId={employeeId}
                    onAnswered={onQuizAnswered}
                  />
                ) : (
                  <Button
                    variant="ai"
                    className="self-start"
                    onClick={() => setOpenQuiz(item.document_id)}
                  >
                    اختبريني في هالدرس
                  </Button>
                )
              )}
            </div>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function AccessDetails({ item }: { item: RoadmapItem }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-faint">
      {item.approver_role && <span>المعتمِد: {item.approver_role}</span>}
      {item.expected_days !== null && <span>المدة المتوقعة: {item.expected_days} أيام</span>}
      {item.procedure_id && (
        <ButtonLink
          variant="secondary"
          className="h-9"
          to={`/procedures?id=${encodeURIComponent(item.procedure_id)}`}
        >
          خطوات الطلب
        </ButtonLink>
      )}
    </div>
  )
}
