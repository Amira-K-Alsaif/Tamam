import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router'
import { ButtonLink } from '../components/Button'
import { MOCK_EMPLOYEE } from '../lib/mockEmployee'
import { MODULES } from '../modules/modules'

const SUGGESTIONS = ['كم رصيد إجازتي السنوية؟', 'كيف أطلب صلاحية نظام؟', 'وش سياسة العمل عن بُعد؟']

export default function HomePage() {
  return (
    <>
      <header className="flex flex-col gap-1">
        <h1 className="m-0 font-display text-3xl font-extrabold">صباح الخير، {MOCK_EMPLOYEE.firstName}</h1>
        <p className="m-0 text-faint">يومك الـ{MOCK_EMPLOYEE.dayNumber} في شركة نخلة للتقنية.</p>
      </header>

      <section
        aria-label="اسأل تمّام"
        className="flex flex-col gap-5 rounded-3xl border border-line bg-surface bg-aurora-glow p-8 sm:p-10"
      >
        <div className="flex items-center gap-4">
          <span aria-hidden="true" className="size-14 shrink-0 rounded-full bg-aurora shadow-2xl shadow-mint/40" />
          <div className="flex flex-col">
            <h2 className="m-0 font-display text-2xl font-semibold">وش تبين تعرفين اليوم؟</h2>
            <span className="text-sm text-muted">إجاباتي من سياسات الشركة وأدلتها، ومعها المصدر دائماً.</span>
          </div>
        </div>
        <ButtonLink to="/chat" variant="ai" className="self-start">
          اسألي تمّام
          <ArrowLeft aria-hidden className="size-4" />
        </ButtonLink>
        <div className="flex flex-wrap gap-2.5">
          {SUGGESTIONS.map((question) => (
            <Link
              key={question}
              to="/chat"
              className="inline-flex h-10 items-center rounded-full border border-line bg-white/5 px-4 text-sm text-soft no-underline"
            >
              {question}
            </Link>
          ))}
        </div>
      </section>

      <ul aria-label="الأقسام" className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 xl:grid-cols-3">
        {MODULES.map(({ id, path, title, summary, icon: Icon }) => (
          <li key={id}>
            <Link
              to={path}
              className="flex h-full flex-col gap-2 rounded-3xl border border-line bg-surface p-6 text-ink no-underline hover:border-mint/40"
            >
              <Icon aria-hidden className="size-6 text-mint" strokeWidth={1.8} />
              <h2 className="m-0 font-display text-lg font-semibold">{title}</h2>
              <p className="m-0 text-sm text-faint">{summary}</p>
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}
