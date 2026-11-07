import { useEffect, useState } from 'react'

import { Card } from '../../components/Card'
import { Diamond } from '../../components/Diamond'
import { PageHeader } from '../../components/PageHeader'
import { ProgressBar } from '../../components/ProgressBar'
import { StatusBadge } from '../../components/StatusBadge'
import type { Status } from '../../components/StatusBadge'
import { getMe, getRoadmap } from '../../lib/api'
import type { AccessStatus, EmployeeProfile, Roadmap, RoadmapItem } from '../../lib/api'
import { moduleById } from '../modules'

const ACCESS_BADGES: Record<AccessStatus, { status: Status; label: string }> = {
  active: { status: 'done', label: 'مفعّلة' },
  requested: { status: 'in-progress', label: 'بانتظار الموافقة' },
  missing: { status: 'missing', label: 'ناقصة' },
}

const KIND_TONES = { access: 'teal', person: 'blue', lesson: 'mint' } as const

type LoadState =
  | { kind: 'loading' }
  | { kind: 'error' }
  | { kind: 'ready'; me: EmployeeProfile; roadmap: Roadmap }

// Owned by team member 5. The new employee's roadmap, grouped by week; see docs/team.md.
export default function OnboardingPage() {
  const info = moduleById('onboarding')
  const [state, setState] = useState<LoadState>({ kind: 'loading' })
  const [selectedWeek, setSelectedWeek] = useState(1)

  useEffect(() => {
    let cancelled = false
    Promise.all([getMe(), getRoadmap()])
      .then(([me, roadmap]) => {
        if (!cancelled) setState({ kind: 'ready', me, roadmap })
      })
      .catch(() => {
        if (!cancelled) setState({ kind: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (state.kind === 'loading') {
    return (
      <>
        <PageHeader title={info.title} description={info.summary} />
        <p className="m-0 text-muted">جاري تجهيز مسارك…</p>
      </>
    )
  }

  if (state.kind === 'error') {
    return (
      <>
        <PageHeader title={info.title} description={info.summary} />
        <Card>
          <p className="m-0 text-danger">ما قدرنا نجيب مسارك. تأكدي إن الخادم شغّال وحاولي مرة ثانية.</p>
        </Card>
      </>
    )
  }

  const { me, roadmap } = state
  const allItems = roadmap.weeks.flatMap((week) => week.items)
  const week = roadmap.weeks.find((w) => w.week === selectedWeek) ?? roadmap.weeks[0]

  return (
    <>
      <PageHeader
        title={info.title}
        description={`أهلاً ${me.full_name} · ${me.job_title}. هذا كل اللي ناقصك، مرتّب بالأسابيع.`}
      />

      <ProgressSummary items={allItems} />

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
                  className={`cursor-pointer rounded-full border px-4 py-1.5 font-body ${
                    selected ? 'border-mint bg-raised text-ink' : 'border-line bg-surface text-muted'
                  }`}
                >
                  الأسبوع {w.week} · {w.items.length}
                </button>
              )
            })}
          </div>

          <ItemsSection title="صلاحيات ناقصة" items={week.items.filter((i) => i.kind === 'access')} />
          <ItemsSection title="أشخاص تقابلهم" items={week.items.filter((i) => i.kind === 'person')} />
          <ItemsSection title="دروس" items={week.items.filter((i) => i.kind === 'lesson')} />
        </>
      )}
    </>
  )
}

function ProgressSummary({ items }: { items: RoadmapItem[] }) {
  const counts = [
    { label: 'صلاحيات ناقصة', value: items.filter((i) => i.kind === 'access').length },
    { label: 'أشخاص تقابلهم', value: items.filter((i) => i.kind === 'person').length },
    { label: 'دروس', value: items.filter((i) => i.kind === 'lesson').length },
  ]
  return (
    <div className="flex flex-wrap gap-4">
      {counts.map((count) => (
        <Card key={count.label} className="min-w-40 flex-1 gap-1">
          <span className="font-display text-3xl font-extrabold">{count.value}</span>
          <span className="text-faint">{count.label}</span>
        </Card>
      ))}
    </div>
  )
}

function ItemsSection({ title, items }: { title: string; items: RoadmapItem[] }) {
  if (items.length === 0) return null
  return (
    <Card title={title}>
      <ul className="m-0 flex list-none flex-col gap-4 p-0">
        {items.map((item) => (
          <li key={`${item.kind}-${item.title}`} className="flex gap-3">
            <span className="pt-2.5">
              <Diamond tone={KIND_TONES[item.kind]} filled={false} />
            </span>
            <div className="flex flex-1 flex-col gap-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong>{item.title}</strong>
                {item.status && <StatusBadge {...ACCESS_BADGES[item.status]} />}
              </div>
              <span className="text-muted">{item.reason}</span>
              {item.kind === 'access' && <AccessDetails item={item} />}
              {item.kind === 'lesson' && item.score !== null && (
                <ProgressBar label="درجتك في التقييم" value={item.score} />
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
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-faint">
      {item.approver_role && <span>المعتمِد: {item.approver_role}</span>}
      {item.expected_days !== null && <span>المدة المتوقعة: {item.expected_days} أيام</span>}
    </div>
  )
}
