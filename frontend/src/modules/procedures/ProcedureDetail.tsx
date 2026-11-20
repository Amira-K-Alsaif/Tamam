import { ArrowRight, Building2, Clock, FileText, UserRound } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Card } from '../../components/Card'
import { Diamond } from '../../components/Diamond'
import { PageHeader } from '../../components/PageHeader'
import type { Procedure, ProcedureSource } from './proceduresApi'
import { ProcedureSteps } from './ProcedureSteps'
import { useChecklist } from './useChecklist'
import { useProcedure } from './useProcedures'

/** One procedure: its steps as a stepper, what to prepare, its forms, and its source. */
export function ProcedureDetail({ id }: { id: string }) {
  const state = useProcedure(id)

  return (
    <>
      <BackLink />
      {state.kind === 'loading' && (
        <p role="status" className="m-0 text-muted">
          جاري تحميل الإجراء…
        </p>
      )}
      {state.kind === 'not-found' && (
        <Card>
          <p role="alert" className="m-0 text-warning">
            ما لقينا هذا الإجراء. ارجعي لكل الإجراءات واختاري واحد منها.
          </p>
        </Card>
      )}
      {state.kind === 'error' && (
        <Card>
          <p role="alert" className="m-0 text-danger">
            ما قدرنا نجيب الإجراء. تأكدي إن الخادم شغّال وحاولي مرة ثانية.
          </p>
        </Card>
      )}
      {state.kind === 'ready' && <ProcedureView procedure={state.procedure} />}
    </>
  )
}

function BackLink() {
  return (
    <Link to="/procedures" className="inline-flex items-center gap-2 self-start text-sm text-muted no-underline hover:text-ink">
      {/* Points right: "back" in a right-to-left layout. */}
      <ArrowRight aria-hidden className="size-4" strokeWidth={1.8} />
      كل الإجراءات
    </Link>
  )
}

function ProcedureView({ procedure }: { procedure: Procedure }) {
  return (
    <>
      <PageHeader title={procedure.title} description={procedure.summary} />

      <div className="flex flex-wrap gap-2.5">
        <Fact icon={Building2} label="القسم">
          {procedure.department}
        </Fact>
        {procedure.owner && (
          <Fact icon={UserRound} label="الجهة المسؤولة">
            {procedure.owner}
          </Fact>
        )}
        {procedure.duration_text && (
          <Fact icon={Clock} label="المدة">
            {procedure.duration_text}
          </Fact>
        )}
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <div className="flex min-w-0 flex-col gap-6 lg:col-span-2">
          <ProcedureSteps procedureId={procedure.id} steps={procedure.steps} />
        </div>
        <div className="flex min-w-0 flex-col gap-6">
          {procedure.requirements.length > 0 && (
            <Requirements procedureId={procedure.id} items={procedure.requirements} />
          )}
          {procedure.forms.length > 0 && <Forms forms={procedure.forms} />}
          <SourceCard source={procedure.source} />
        </div>
      </div>
    </>
  )
}

function Fact({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <span className="inline-flex h-10 items-center gap-2 rounded-full border border-line bg-surface px-4 text-sm">
      <Icon aria-hidden className="size-4 text-faint" strokeWidth={1.8} />
      <span className="text-faint">{label}:</span>
      <span className="text-ink">{children}</span>
    </span>
  )
}

function Requirements({ procedureId, items }: { procedureId: string; items: string[] }) {
  const checklist = useChecklist(`${procedureId}.requirements`)
  const ready = items.filter((item) => checklist.isChecked(item)).length

  return (
    <Card title="جهّزي قبل ما تبدئين">
      <span className="text-sm text-faint">
        جاهز {ready} من {items.length}
      </span>
      <ul aria-label="المتطلبات" className="m-0 flex list-none flex-col gap-3 p-0">
        {items.map((item, index) => {
          const inputId = `${procedureId}-requirement-${index}`
          return (
            <li key={item}>
              <label htmlFor={inputId} className="flex cursor-pointer items-start gap-3 text-soft">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={checklist.isChecked(item)}
                  onChange={() => checklist.toggle(item)}
                  className="mt-1.5 size-4 shrink-0 cursor-pointer accent-mint"
                />
                <span className={checklist.isChecked(item) ? 'text-faint line-through' : ''}>{item}</span>
              </label>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

function Forms({ forms }: { forms: string[] }) {
  return (
    <Card title="النماذج">
      <ul aria-label="النماذج المطلوبة" className="m-0 flex list-none flex-col gap-3 p-0">
        {forms.map((form) => (
          <li key={form} className="flex items-center gap-3">
            <FileText aria-hidden className="size-4 shrink-0 text-blue-soft" strokeWidth={1.8} />
            <span>{form}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function SourceCard({ source }: { source: ProcedureSource }) {
  const location = [source.page !== null && `صفحة ${source.page}`, source.section_title].filter(Boolean).join(' · ')

  return (
    <section aria-label="مصدر الإجراء" className="flex flex-col gap-3 rounded-3xl border border-mint/20 bg-sunken p-6">
      <h2 className="m-0 font-display text-lg font-semibold">المصدر</h2>
      <div className="flex flex-wrap items-center gap-2">
        <Diamond tone="teal" />
        <strong>{source.document_title}</strong>
        {location && <span className="text-xs text-faint">{location}</span>}
      </div>
      <blockquote className="m-0 rounded-xl bg-mint/10 px-3 py-2 text-sm leading-relaxed text-soft">
        «{source.quote}»
      </blockquote>
    </section>
  )
}
