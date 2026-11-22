import type { Source } from '../../lib/api'

/** The sources of the latest answer, numbered to match its [1], [2] citations. */
export function SourcesPanel({ sources }: { sources: Source[] }) {
  return (
    <aside aria-label="مصادر الإجابة" className="side-column flex flex-col gap-3">
      <h2 className="m-0 font-display text-lg font-semibold">مصادر الإجابة</h2>
      {sources.length === 0 ? (
        <p className="m-0 text-sm text-faint">بتظهر هنا مصادر آخر إجابة.</p>
      ) : (
        sources.map((source, index) => (
          <article
            key={`${source.document_id}-${source.section_title}`}
            className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4"
          >
            <strong className="text-sm">
              [{index + 1}] {source.document_title}
            </strong>
            <span className="text-xs text-faint">
              {source.page === null ? '' : `صفحة ${source.page} · `}
              {source.section_title}
            </span>
            <p className="m-0 text-sm leading-relaxed text-soft">{source.quote}</p>
          </article>
        ))
      )}
    </aside>
  )
}
