import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { EmployeeProfile, Progress, Roadmap } from '../../lib/api'
import OnboardingPage from './OnboardingPage'

const NOURA: EmployeeProfile = {
  id: 'emp-004',
  full_name: 'نورة العتيبي',
  department_id: 'dep-data',
  team: 'البيانات والتحليلات',
  job_title: 'محللة بيانات',
  manager_id: 'emp-002',
  years_of_experience: 0,
  role: 'employee',
}
const SARA: EmployeeProfile = { ...NOURA, id: 'emp-002', full_name: 'سارة القحطاني', job_title: 'مديرة البيانات' }

const ITEM = {
  score: null,
  access_item_id: null,
  status: null,
  procedure_id: null,
  approver_role: null,
  expected_days: null,
  employee_id: null,
  topic: null,
  document_id: null,
}

const ROADMAP: Roadmap = {
  employee_id: 'emp-004',
  weeks: [
    {
      week: 1,
      items: [
        {
          ...ITEM,
          kind: 'access',
          title: 'الشبكة الخاصة (VPN)',
          reason: 'مطلوبة لمسمى محللة بيانات.',
          week: 1,
          status: 'requested',
          procedure_id: 'proc-vpn',
          approver_role: 'مسؤول الصلاحيات',
          expected_days: 3,
        },
        {
          ...ITEM,
          kind: 'person',
          title: 'فهد المطيري · مسؤول الصلاحيات',
          reason: 'يوافق على الشبكة الخاصة (VPN)',
          week: 1,
          employee_id: 'emp-005',
        },
        {
          ...ITEM,
          kind: 'lesson',
          title: 'درس: أمن المعلومات',
          reason: 'درجتك في التقييم 40 من 100، والمطلوب 70.',
          week: 1,
          score: 40,
          topic: 'أمن المعلومات',
          document_id: 'infosec',
        },
      ],
    },
  ],
}

const PROGRESS: Progress = {
  employee_id: 'emp-004',
  access_active: 2,
  access_total: 5,
  topics_passed: 1,
  topics_total: 5,
  percent: 30,
  badges: [
    { id: 'first-step', title: 'أول خطوة', description: 'خلّصت التقييم الأولي', earned: true },
    { id: 'tamam', title: 'تمّام', description: 'أكملت مسارك كامل', earned: false },
  ],
}

const QUIZ = {
  topic: 'أمن المعلومات',
  document_id: 'infosec',
  document_title: 'سياسة أمن المعلومات',
  questions: [
    {
      question: 'وش تسوي برموز التحقق؟',
      options: ['أرسلها لزميلي', 'لا أرسلها لأحد'],
      source: {
        document_id: 'infosec',
        document_title: 'سياسة أمن المعلومات',
        section_title: 'قواعد عامة',
        quote: 'لا ترسل رموز التحقق لأحد.',
      },
    },
  ],
}

const ROUTES: Record<string, unknown> = {
  '/api/onboarding/demo-employees': [NOURA, SARA],
  '/api/onboarding/me?employee_id=emp-004': { ...NOURA, manager_name: 'سارة القحطاني' },
  '/api/onboarding/roadmap?employee_id=emp-004': ROADMAP,
  '/api/onboarding/progress?employee_id=emp-004': PROGRESS,
  '/api/onboarding/team?employee_id=emp-004': [],
  '/api/onboarding/me?employee_id=emp-002': { ...SARA, manager_name: null },
  '/api/onboarding/roadmap?employee_id=emp-002': { employee_id: 'emp-002', weeks: [] },
  '/api/onboarding/progress?employee_id=emp-002': { ...PROGRESS, employee_id: 'emp-002', percent: 100 },
  '/api/onboarding/team?employee_id=emp-002': [{ employee: NOURA, progress: PROGRESS, next_step: 'الشبكة الخاصة (VPN)' }],
  '/api/onboarding/lessons/infosec/quiz': QUIZ,
  '/api/onboarding/lessons/infosec/attempt?employee_id=emp-004': {
    topic: 'أمن المعلومات',
    score: 100,
    passed: true,
    correct: [true],
    correct_options: [1],
  },
}

function serve(overrides: Record<string, unknown> = {}) {
  const routes = { ...ROUTES, ...overrides }
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = new URL(String(input))
    const body = routes[url.pathname + url.search]
    return new Response(body === undefined ? '' : JSON.stringify(body), { status: body === undefined ? 404 : 200 })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderPage() {
  render(
    <MemoryRouter>
      <OnboardingPage />
    </MemoryRouter>,
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('OnboardingPage', () => {
  it('shows progress, badges, and a link to the steps of each missing access', async () => {
    serve()
    renderPage()

    expect(await screen.findByText(/أهلاً نورة العتيبي/)).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'تقدّمك في المسار' })).toHaveAttribute('aria-valuenow', '30')
    expect(screen.getByText('أول خطوة')).toBeInTheDocument()
    expect(screen.getByText('1 من 2')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'خطوات الطلب' })).toHaveAttribute('href', '/procedures?id=proc-vpn')
  })

  it('links each person to meet to their card in the company map', async () => {
    serve()
    renderPage()

    expect(await screen.findByRole('link', { name: 'افتحي بطاقته في خريطة الشركة' })).toHaveAttribute(
      'href',
      '/org-map?person=emp-005',
    )
  })

  it("shows the manager's team when the demo switches to a manager", async () => {
    serve()
    renderPage()
    await screen.findByText(/أهلاً نورة العتيبي/)

    await userEvent.selectOptions(screen.getByRole('combobox'), 'emp-002')

    expect(await screen.findByText('فريقي')).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'الخطوة الجاية: الشبكة الخاصة (VPN)' })).toBeInTheDocument()
  })

  it('starts a new hire with the assessment and reloads the path after answering', async () => {
    const fetchMock = serve({
      '/api/onboarding/progress?employee_id=emp-004': { ...PROGRESS, topics_passed: 0, topics_total: 0 },
      '/api/onboarding/assessment': {
        questions: [{ ...QUIZ.questions[0], topic: 'أمن المعلومات' }],
      },
      '/api/onboarding/assessment/attempt?employee_id=emp-004': {
        scores: [{ topic: 'أمن المعلومات', score: 0, passed: false }],
        correct: [false],
        correct_options: [1],
      },
    })
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: 'ابدئي التقييم' }))
    await userEvent.click(await screen.findByLabelText('أرسلها لزميلي'))
    await userEvent.click(screen.getByRole('button', { name: 'سلّمي الإجابات' }))

    expect(
      await screen.findByRole('progressbar', { name: 'أمن المعلومات: صار درس في مسارك' }),
    ).toHaveAttribute('aria-valuenow', '0')
    await userEvent.click(screen.getByRole('button', { name: 'اعرضي مساري' }))
    const progressCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/progress?employee_id=emp-004'))
    expect(progressCalls.length).toBe(2)
  })

  it('hides the assessment once the employee has scores', async () => {
    serve()
    renderPage()

    await screen.findByText(/أهلاً نورة العتيبي/)
    expect(screen.queryByRole('button', { name: 'ابدئي التقييم' })).not.toBeInTheDocument()
  })

  it('takes a lesson quiz and reloads the roadmap after answering', async () => {
    const fetchMock = serve()
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: 'اختبريني في هالدرس' }))
    await userEvent.click(await screen.findByLabelText('لا أرسلها لأحد'))
    await userEvent.click(screen.getByRole('button', { name: 'سلّمي الإجابات' }))

    expect(await screen.findByText(/نجحتي، والدرس طلع من مسارك/)).toBeInTheDocument()
    const roadmapCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/roadmap?employee_id=emp-004'))
    expect(roadmapCalls.length).toBe(2)
  })
})
