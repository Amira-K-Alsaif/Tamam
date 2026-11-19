import type { SearchResponse } from './orgMapApi'
import { PersonAvatar } from './PersonAvatar'

type SearchResultsProps = {
  result: SearchResponse | null
  loading: boolean
  error: boolean
  onPick: (personId: string, departmentId: string) => void
  onClear: () => void
}

/** The answer to "who do I talk to about X?". */
export function SearchResults({ result, loading, error, onPick, onClear }: SearchResultsProps) {
  if (!result && !loading && !error) return null

  return (
    <section
      aria-label="نتائج البحث"
      className="flex flex-col gap-3 rounded-3xl border border-line bg-surface p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 className="m-0 font-display text-base font-semibold">
          {result ? `نتائج «${result.query}»` : 'نتائج البحث'}
        </h2>
        <button type="button" onClick={onClear} className="text-xs text-faint hover:text-ink">
          إغلاق
        </button>
      </div>

      {loading && <p className="m-0 text-sm text-faint">جارٍ البحث…</p>}
      {error && (
        <p role="alert" className="m-0 text-sm text-danger">
          تعذّر البحث. تأكد إن الخادم شغال وحاول مرة ثانية.
        </p>
      )}
      {result && result.hits.length === 0 && (
        <p className="m-0 text-sm text-faint">ما لقيت أحد مسؤول عن هذا. جرّب كلمة ثانية.</p>
      )}
      {result && result.hits.length > 0 && (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {result.hits.map(({ person, department_name, matched_topic }) => (
            <li key={person.id}>
              <button
                type="button"
                onClick={() => onPick(person.id, person.department_id)}
                className="flex w-full flex-wrap items-center gap-3 rounded-2xl border border-line bg-sunken p-3 text-start hover:border-mint/40"
              >
                <PersonAvatar person={person} />
                <span className="flex min-w-0 flex-1 flex-col leading-normal">
                  <strong className="text-sm">{person.full_name}</strong>
                  <span className="text-xs text-faint">
                    {person.job_title} · {department_name}
                  </span>
                </span>
                <span className="inline-flex h-7 items-center rounded-full bg-mint/12 px-3 text-xs text-mint">
                  {matched_topic}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
