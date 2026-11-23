import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { AppShell } from './components/AppShell'
import HomePage from './pages/HomePage'

// Each module page loads when it is first opened, so the first visit downloads the home page
// and the shell only, not all six modules.
const ChatPage = lazy(() => import('./modules/chat/ChatPage'))
const ProceduresPage = lazy(() => import('./modules/procedures/ProceduresPage'))
const OrgMapPage = lazy(() => import('./modules/org-map/OrgMapPage'))
const OnboardingPage = lazy(() => import('./modules/onboarding/OnboardingPage'))
const CareerPage = lazy(() => import('./modules/career/CareerPage'))
const KnowledgePage = lazy(() => import('./modules/knowledge/KnowledgePage'))

function Page({ children }: { children: ReactNode }) {
  return (
    <Suspense
      fallback={
        <p role="status" className="m-0 text-muted">
          جاري التحميل…
        </p>
      }
    >
      {children}
    </Suspense>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="chat" element={<Page><ChatPage /></Page>} />
        <Route path="procedures" element={<Page><ProceduresPage /></Page>} />
        <Route path="org-map" element={<Page><OrgMapPage /></Page>} />
        <Route path="onboarding" element={<Page><OnboardingPage /></Page>} />
        <Route path="career" element={<Page><CareerPage /></Page>} />
        <Route path="knowledge" element={<Page><KnowledgePage /></Page>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
