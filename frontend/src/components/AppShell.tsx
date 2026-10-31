import { House } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import logo from '../assets/logo-white.png'
import { getHealth } from '../lib/api'
import { MOCK_EMPLOYEE } from '../lib/mockEmployee'
import { MODULES } from '../modules/modules'

type BackendState = 'checking' | 'online' | 'offline'

const BACKEND_LABEL: Record<BackendState, string> = {
  checking: 'جارٍ التحقق من الخادم…',
  online: 'الخادم متصل',
  offline: 'الخادم غير متصل',
}

function SideLink({ to, label, icon: Icon }: { to: string; label: string; icon: LucideIcon }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `flex h-11 items-center gap-3 rounded-xl px-3.5 text-sm no-underline ${
          isActive ? 'bg-mint/10 text-ink' : 'text-muted hover:bg-white/5'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon aria-hidden className={`size-5 ${isActive ? 'text-mint' : ''}`} strokeWidth={1.8} />
          {label}
        </>
      )}
    </NavLink>
  )
}

export function AppShell() {
  const [backend, setBackend] = useState<BackendState>('checking')

  useEffect(() => {
    getHealth()
      .then(() => setBackend('online'))
      .catch(() => setBackend('offline'))
  }, [])

  const employeeModules = MODULES.filter((m) => !m.adminOnly)
  const adminModules = MODULES.filter((m) => m.adminOnly)

  return (
    <div className="flex min-h-screen flex-wrap">
      <nav
        aria-label="القائمة الرئيسية"
        className="flex side-column flex-col gap-7 border-e border-line bg-sidebar px-4 py-7"
      >
        <img src={logo} alt="تمّام" className="ms-2.5 w-24" />
        <div className="flex flex-col gap-1">
          <SideLink to="/" label="الرئيسية" icon={House} />
          {employeeModules.map((m) => (
            <SideLink key={m.id} to={m.path} label={m.title} icon={m.icon} />
          ))}
        </div>
        {adminModules.length > 0 && (
          <div className="flex flex-col gap-1 border-t border-line pt-4">
            <span className="px-3.5 pb-1.5 text-xs text-faint">للمشرفين</span>
            {adminModules.map((m) => (
              <SideLink key={m.id} to={m.path} label={m.title} icon={m.icon} />
            ))}
          </div>
        )}
        <div className="mt-auto flex flex-col gap-3">
          <p role="status" className={`m-0 px-3.5 text-xs ${backend === 'online' ? 'text-mint' : 'text-faint'}`}>
            {BACKEND_LABEL[backend]}
          </p>
          <div className="flex items-center gap-3 rounded-2xl bg-surface p-3">
            <span className="flex size-10 items-center justify-center rounded-full bg-aurora font-semibold text-night">
              {MOCK_EMPLOYEE.firstName[0]}
            </span>
            <span className="flex flex-col text-xs leading-normal">
              <strong className="text-sm">{MOCK_EMPLOYEE.fullName}</strong>
              <span className="text-faint">{MOCK_EMPLOYEE.jobTitle}</span>
            </span>
          </div>
        </div>
      </nav>

      <main className="flex min-w-0 main-column flex-col gap-7 px-6 py-8 sm:px-10">
        <Outlet />
      </main>
    </div>
  )
}
