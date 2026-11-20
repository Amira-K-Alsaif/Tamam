import { Diamond } from '../../components/Diamond'
import type { ProcedureSource } from './proceduresApi'

/** Where a procedure or form comes from: the document, its section, and the quoted text. */
export function SourceCard({ source, label }: { source: ProcedureSource; label: string }) {
  const location = [source.page !== null && `صفحة ${source.page}`, source.section_title].filter(Boolean).join(' · ')

  return (
    <section aria-label={label} className="flex flex-col gap-3 rounded-3xl border border-mint/20 bg-sunken p-6">
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
