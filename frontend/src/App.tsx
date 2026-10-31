import { Navigate, Route, Routes } from 'react-router'
import { AppShell } from './components/AppShell'
import CareerPage from './modules/career/CareerPage'
import ChatPage from './modules/chat/ChatPage'
import KnowledgePage from './modules/knowledge/KnowledgePage'
import OnboardingPage from './modules/onboarding/OnboardingPage'
import OrgMapPage from './modules/org-map/OrgMapPage'
import ProceduresPage from './modules/procedures/ProceduresPage'
import HomePage from './pages/HomePage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="procedures" element={<ProceduresPage />} />
        <Route path="org-map" element={<OrgMapPage />} />
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="career" element={<CareerPage />} />
        <Route path="knowledge" element={<KnowledgePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
