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
  skill_id: null,
  level: null,
  expected_level: null,
}

const ROADMAP: Roadmap = {
  employee_id: 'emp-004',
  assessed: true,
  drawn_by: 'ai',
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
  skills_ready: 0,
  skills_total: 0,
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
  '/api/onboarding/roadmap?employee_id=emp-002': { employee_id: 'emp-002', assessed: true, drawn_by: 'rules', weeks: [] },
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

  it('starts with the assessment, then shows the path drawn from the result', async () => {
    const fetchMock = serve({
      '/api/onboarding/roadmap?employee_id=emp-004': { employee_id: 'emp-004', assessed: false, drawn_by: 'rules', weeks: [] },
      '/api/onboarding/assessment?employee_id=emp-004': {
        questions: [
          { ...QUIZ.questions[0], kind: 'company', topic: 'سياسة أمن المعلومات', skill_id: null },
          {
            kind: 'skill',
            topic: 'تحليل البيانات',
            question: 'وين مستواك في تحليل البيانات؟',
            options: ['ما أعرفها', 'مبتدئ', 'متوسط', 'متقدم', 'خبير'],
            source: null,
            skill_id: 7,
          },
        ],
      },
      '/api/onboarding/assessment/attempt?employee_id=emp-004': {
        topics: [{ topic: 'سياسة أمن المعلومات', document_id: 'infosec', score: 0, passed: false }],
        skills: [{ skill_id: 7, label_ar: 'تحليل البيانات', level: 2, expected_level: 4 }],
        correct: [false, null],
        correct_options: [1, null],
      },
    })
    renderPage()

    expect(await screen.findByText('قبل ما نبدأ: تقييمك الأولي')).toBeInTheDocument()
    expect(screen.queryByText('شاراتك')).not.toBeInTheDocument()

    expect(await screen.findByText('عن الشركة')).toBeInTheDocument()
    expect(screen.getByText('عن تخصصك: وين مستواك؟')).toBeInTheDocument()
    await userEvent.click(screen.getByLabelText('أرسلها لزميلي'))
    await userEvent.click(screen.getByLabelText('متوسط'))
    await userEvent.click(screen.getByRole('button', { name: 'سلّمي الإجابات' }))

    expect(
      await screen.findByRole('progressbar', { name: 'سياسة أمن المعلومات: صارت درس في مسارك' }),
    ).toHaveAttribute('aria-valuenow', '0')
    expect(
      screen.getByRole('progressbar', { name: 'تحليل البيانات: مستواك 2 من 4، ومسماك يحتاج 4' }),
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'اعرضي مساري' }))
    const roadmapCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/roadmap?employee_id=emp-004'))
    expect(roadmapCalls.length).toBe(2)
  })

  it('says so when the assessment cannot load', async () => {
    serve({
      '/api/onboarding/roadmap?employee_id=emp-004': { employee_id: 'emp-004', assessed: false, drawn_by: 'rules', weeks: [] },
    })
    renderPage()

    expect(await screen.findByText('التقييم ما تجهّز. حاولي مرة ثانية بعد شوي.')).toBeInTheDocument()
  })

  it('shows the path, not the assessment, once the employee is assessed', async () => {
    serve()
    renderPage()

    await screen.findByText(/أهلاً نورة العتيبي/)
    expect(screen.queryByText('قبل ما نبدأ: تقييمك الأولي')).not.toBeInTheDocument()
    expect(screen.getByText('رتّب تمّام دروسك ومهاراتك من نتيجة تقييمك الأولي.')).toBeInTheDocument()
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
