import { FileText, Sparkles } from 'lucide-react'
import { Link } from 'react-router'
import { arabicCount, FIELDS } from './arabicCount'
import { useCompanyForms } from './useProcedures'

/** The company forms, each opening «عبّي النموذج عني». Hidden when there are none. */
export function FormsSection() {
  const state = useCompanyForms()

  if (state.kind === 'loading' || (state.kind === 'ready' && state.forms.length === 0)) return null

  return (
    <section aria-labelledby="forms-heading" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="forms-heading" className="m-0 font-display text-2xl font-semibold">
          النماذج
        </h2>
        <p className="m-0 text-sm text-faint">تمّام يعبّي لك اللي يعرفه من ملفك، وأنتِ تكمّلين الباقي.</p>
      </div>

      {state.kind === 'error' ? (
        <p role="alert" className="m-0 text-danger">
          ما قدرنا نجيب النماذج. تأكدي إن الخادم شغّال وحاولي مرة ثانية.
        </p>
      ) : (
        <ul aria-label="النماذج" className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 xl:grid-cols-3">
          {state.forms.map((form) => (
            <li key={form.id}>
              <Link
                to={`?form=${encodeURIComponent(form.id)}`}
                className="flex h-full flex-col gap-3 rounded-3xl border border-line bg-surface p-6 text-ink no-underline hover:border-blue/50"
              >
                <FileText aria-hidden className="size-6 text-blue-soft" strokeWidth={1.8} />
                <h3 className="m-0 font-display text-lg font-semibold">{form.title}</h3>
                <span className="text-sm text-faint">
                  {form.department} · {arabicCount(form.fields.length, FIELDS)}
                </span>
                <span className="mt-auto inline-flex items-center gap-1.5 pt-1 text-sm text-mint">
                  <Sparkles aria-hidden className="size-4" strokeWidth={1.8} />
                  عبّي النموذج عني
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
