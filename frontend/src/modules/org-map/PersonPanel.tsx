import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { contactHeading, proceduresHeading, relationLabel } from './labels'
import type { PersonDetail } from './orgMapApi'
import { PersonAvatar } from './PersonAvatar'

type PersonPanelProps = {
  person: PersonDetail | null
  loading: boolean
  error: boolean
}

function Heading({ children }: { children: string }) {
  return <h3 className="m-0 text-xs font-normal text-faint">{children}</h3>
}

/** Who the selected person is, what to contact them about, and how to reach them. */
export function PersonPanel({ person, loading, error }: PersonPanelProps) {
  const frame = 'side-column flex flex-col gap-5 self-start rounded-3xl border border-line bg-surface p-6'

  if (error) {
    return (
      <aside aria-label="بطاقة الشخص" className={frame}>
        <p role="alert" className="m-0 text-sm text-danger">
          تعذّر تحميل بيانات هذا الشخص. اختر شخصاً ثانياً أو أعد المحاولة.
        </p>
      </aside>
    )
  }
  if (!person) {
    return (
      <aside aria-label="بطاقة الشخص" className={frame}>
        <p className="m-0 text-sm text-faint">{loading ? 'جارٍ التحميل…' : 'اختر أي شخص في الخريطة لتعرف عنه.'}</p>
      </aside>
    )
  }

  const relation = relationLabel(person)

  return (
    <aside aria-label="بطاقة الشخص" aria-busy={loading} className={frame}>
      <div className="flex items-center gap-4">
        <PersonAvatar person={person} size="lg" />
        <div className="flex min-w-0 flex-col">
          <h2 className="m-0 font-display text-xl font-semibold">{person.full_name}</h2>
          <span className="text-sm text-faint">{person.job_title}</span>
        </div>
      </div>
      {relation && (
        <span className="inline-flex h-7 items-center self-start rounded-full bg-mint/12 px-3 text-xs text-mint">
          {relation}
        </span>
      )}

      {person.contact_topics.length > 0 && (
        <div className="flex flex-col gap-2.5">
          <Heading>{contactHeading(person)}</Heading>
          <ul className="m-0 flex list-none flex-wrap gap-2 p-0">
            {person.contact_topics.map((topic) => (
              <li
                key={topic}
                className="inline-flex h-8 items-center rounded-full border border-line-strong px-3 text-xs text-soft"
              >
                {topic}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-col gap-2.5">
        <Heading>التواصل</Heading>
        <dl className="m-0 flex flex-col gap-2">
          <div className="flex items-center justify-between gap-3 rounded-xl bg-sunken px-4 py-3 text-sm">
            <dt className="text-faint">البريد</dt>
            <dd dir="ltr" className="m-0 min-w-0 truncate">
              {person.email}
            </dd>
          </div>
          <div className="flex items-center justify-between gap-3 rounded-xl bg-sunken px-4 py-3 text-sm">
            <dt className="text-faint">المكتب</dt>
            <dd className="m-0">{person.office}</dd>
          </div>
        </dl>
      </div>

      {person.procedures.length > 0 && (
        <div className="flex flex-col gap-2.5">
          <Heading>{proceduresHeading(person)}</Heading>
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {person.procedures.map((procedure) => (
              <li key={procedure.id}>
                <Link
                  to="/procedures"
                  className="flex items-center justify-between gap-3 rounded-xl bg-sunken px-4 py-3 text-sm text-ink no-underline hover:bg-raised"
                >
                  {procedure.title}
                  {/* Points left: "forward" in a right-to-left layout. */}
                  <ArrowLeft aria-hidden className="size-4 text-mint" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  )
}
