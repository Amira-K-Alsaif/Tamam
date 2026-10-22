import { useEffect, useState } from 'react'
import { getHealth } from './lib/api'
import { MODULES } from './modules/modules'

type BackendState = 'checking' | 'online' | 'offline'

const BACKEND_LABEL: Record<BackendState, string> = {
  checking: 'جارٍ التحقق من الخادم…',
  online: 'الخادم متصل',
  offline: 'الخادم غير متصل',
}

export default function App() {
  const [backend, setBackend] = useState<BackendState>('checking')

  useEffect(() => {
    getHealth()
      .then(() => setBackend('online'))
      .catch(() => setBackend('offline'))
  }, [])

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-4xl font-bold">تمّام</h1>
        <p className="text-muted">رفيقك الذكي لفهم أنظمة الشركة، من أول سؤال إلى أول إنجاز.</p>
        <p role="status" className={backend === 'online' ? 'text-accent' : 'text-muted'}>
          {BACKEND_LABEL[backend]}
        </p>
      </header>

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map(({ id, title, summary, icon: Icon }) => (
          <li key={id} className="flex flex-col gap-2 rounded-xl border border-line bg-surface p-5">
            <Icon aria-hidden className="size-6 text-accent" />
            <h2 className="font-display text-lg">{title}</h2>
            <p className="text-sm text-muted">{summary}</p>
          </li>
        ))}
      </ul>
    </main>
  )
}
