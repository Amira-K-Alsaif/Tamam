import { Clock, FileText, ListOrdered, Search } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { Card } from '../../components/Card'
import { Diamond } from '../../components/Diamond'
import { arabicCount, FORMS, PROCEDURES, STEPS } from './arabicCount'
import type { Procedure } from './proceduresApi'
import { useProcedureCatalog } from './useProcedures'

/** The searchable list of every procedure, filtered by department. */
export function ProcedureCatalog() {
  const [query, setQuery] = useState('')
  const [department, setDepartment] = useState<string | null>(null)
  const { state, departments } = useProcedureCatalog(query, department)
  const filtering = query.trim() !== '' || department !== null

  return (
    <>
      <div className="flex flex-col gap-4">
        <div className="flex h-14 items-center gap-3 rounded-full border border-mint/35 bg-surface px-5 focus-within:border-mint">
          <Search aria-hidden className="size-5 shrink-0 text-faint" strokeWidth={1.8} />
          <label htmlFor="procedure-search" className="sr-only">
            ابحث عن إجراء
          </label>
          <input
            id="procedure-search"
            type="text"
            enterKeyHint="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="ابحث عن إجراء أو نموذج… مثلاً: إجازة، VPN، تعويض"
            className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none placeholder:text-faint"
          />
        </div>

        {departments.length > 1 && (
          <div role="group" aria-label="تصفية حسب القسم" className="flex flex-wrap gap-2">
            <FilterChip label="كل الأقسام" selected={department === null} onClick={() => setDepartment(null)} />
            {departments.map((d) => (
              <FilterChip key={d} label={d} selected={department === d} onClick={() => setDepartment(d)} />
            ))}
          </div>
        )}
      </div>

      {state.kind === 'loading' && (
        <p role="status" className="m-0 text-muted">
          جاري تحميل الإجراءات…
        </p>
      )}

      {state.kind === 'error' && (
        <Card>
          <p role="alert" className="m-0 text-danger">
            ما قدرنا نجيب الإجراءات. تأكدي إن الخادم شغّال وحاولي مرة ثانية.
          </p>
        </Card>
      )}

      {state.kind === 'ready' && state.procedures.length === 0 && (
        <Card>
          <div className="flex items-center gap-3">
            <Diamond filled={false} />
            <strong>{filtering ? 'ما لقينا إجراء يطابق بحثك.' : 'ما فيه إجراءات بعد.'}</strong>
          </div>
          <p className="m-0 text-muted">
            {filtering
              ? 'جرّبي كلمة ثانية أو اختاري «كل الأقسام».'
              : 'بتظهر الإجراءات هنا أول ما تُستخرج من وثائق الشركة.'}
          </p>
        </Card>
      )}

      {state.kind === 'ready' && state.procedures.length > 0 && (
        <>
          <p role="status" className="m-0 text-sm text-faint">
            {arabicCount(state.procedures.length, PROCEDURES)}
          </p>
          <ul aria-label="الإجراءات" className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 xl:grid-cols-3">
            {state.procedures.map((procedure) => (
              <li key={procedure.id}>
                <ProcedureCard procedure={procedure} />
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}

function FilterChip({ label, selected, onClick }: { label: string; selected: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`cursor-pointer rounded-full border px-4 py-1.5 font-body text-sm ${
        selected ? 'border-mint bg-raised text-ink' : 'border-line bg-surface text-muted hover:text-ink'
      }`}
    >
      {label}
    </button>
  )
}

function ProcedureCard({ procedure }: { procedure: Procedure }) {
  return (
    <Link
      to={`?id=${encodeURIComponent(procedure.id)}`}
      className="flex h-full flex-col gap-3 rounded-3xl border border-line bg-surface p-6 text-ink no-underline hover:border-mint/40"
    >
      <span className="text-xs text-mint">{procedure.department}</span>
      <h2 className="m-0 font-display text-lg font-semibold">{procedure.title}</h2>
      <p className="m-0 line-clamp-2 text-sm text-faint">{procedure.summary}</p>
      <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 pt-1 text-xs text-muted">
        <Meta icon={ListOrdered}>{arabicCount(procedure.steps.length, STEPS)}</Meta>
        {procedure.duration_text && <Meta icon={Clock}>{procedure.duration_text}</Meta>}
        {procedure.forms.length > 0 && <Meta icon={FileText}>{arabicCount(procedure.forms.length, FORMS)}</Meta>}
      </div>
    </Link>
  )
}

function Meta({ icon: Icon, children }: { icon: LucideIcon; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Icon aria-hidden className="size-3.5" strokeWidth={1.8} />
      {children}
    </span>
  )
}
