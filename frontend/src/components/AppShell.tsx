import { House, Menu, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import logo from '../assets/logo-white.png'
import { MOCK_EMPLOYEE } from '../lib/mockEmployee'
import { MODULES } from '../modules/modules'

function SideLink({
  to,
  label,
  icon: Icon,
  onNavigate,
}: {
  to: string
  label: string
  icon: LucideIcon
  onNavigate: () => void
}) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      onClick={onNavigate}
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

// The side menu on wide screens. On phones it folds behind a menu button in a slim top bar,
// so each page starts with its own content instead of the whole menu.
export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false)
  const employeeModules = MODULES.filter((m) => !m.adminOnly)
  const adminModules = MODULES.filter((m) => m.adminOnly)
  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <header className="flex items-center justify-between border-b border-line bg-sidebar px-4 py-3 md:hidden">
        <img src={logo} alt="تمّام" className="w-16" />
        <button
          type="button"
          aria-expanded={menuOpen}
          aria-controls="main-menu"
          onClick={() => setMenuOpen((open) => !open)}
          className="flex size-10 cursor-pointer items-center justify-center rounded-xl text-ink hover:bg-white/5"
        >
          {menuOpen ? <X aria-hidden className="size-5" /> : <Menu aria-hidden className="size-5" />}
          <span className="sr-only">{menuOpen ? 'إغلاق القائمة' : 'القائمة'}</span>
        </button>
      </header>

      <nav
        id="main-menu"
        aria-label="القائمة الرئيسية"
        className={`${menuOpen ? 'flex' : 'hidden'} flex-col gap-7 border-b border-line bg-sidebar px-4 py-5 md:sticky md:top-0 md:flex md:h-screen md:w-64 md:shrink-0 md:border-e md:border-b-0 md:py-7`}
      >
        <img src={logo} alt="تمّام" className="ms-2.5 hidden w-24 md:block" />
        <div className="flex flex-col gap-1">
          <SideLink to="/" label="الرئيسية" icon={House} onNavigate={closeMenu} />
          {employeeModules.map((m) => (
            <SideLink key={m.id} to={m.path} label={m.title} icon={m.icon} onNavigate={closeMenu} />
          ))}
        </div>
        {adminModules.length > 0 && (
          <div className="flex flex-col gap-1 border-t border-line pt-4">
            <span className="px-3.5 pb-1.5 text-xs text-faint">للمشرفين</span>
            {adminModules.map((m) => (
              <SideLink key={m.id} to={m.path} label={m.title} icon={m.icon} onNavigate={closeMenu} />
            ))}
          </div>
        )}
        <div className="mt-auto flex flex-col gap-3">
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

      <main className="flex min-w-0 flex-1 flex-col gap-7 px-5 py-6 sm:px-10 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}
