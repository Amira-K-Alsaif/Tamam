import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { DevelopmentPlan, GapAnalysis, JobTitle } from './api'
import CareerPage from './CareerPage'

const TITLES: JobTitle[] = [
  { id: 7, code: 'FIN-1', ladder: 'finance', level: 'mid', name_ar: 'محاسب', name_en: 'Accountant', next_title_id: 8, esco_occupation_uri: 'http://data.europa.eu/esco/occupation/eda0d957-3c3c-4139-b89a-a18bc9e18897', postings_count: 19 },
  { id: 8, code: 'FIN-2', ladder: 'finance', level: 'manager', name_ar: 'مدير مالي', name_en: 'Finance Manager', next_title_id: null, esco_occupation_uri: 'http://data.europa.eu/esco/occupation/30f3ea93-882a-4525-841c-1d5b4b64076f', postings_count: 16 },
]

const skill = (id: number, label: string, expected: number, level: number, frequency: number) => ({
  skill_id: id,
  label_ar: label,
  label_en: label,
  market_frequency: frequency,
  expected_level: expected,
  employee_level: level,
})

const GAP: GapAnalysis = {
  current_title_id: 7,
  target_title_id: 8,
  readiness_score: 42,
  level_source: 'current_title_market_proxy',
  gap: {
    matched: [skill(1, 'إعداد القوائم المالية', 4, 4, 0.69)],
    to_improve: [skill(2, 'إعداد الموازنات', 4, 2, 0.94)],
    missing: [{ ...skill(3, 'قيادة الفرق', 4, 0, 0.81), priority: 'high' }],
    evidence_postings: 16,
    low_evidence: false,
  },
  radar: [skill(2, 'إعداد الموازنات', 4, 2, 0.94), skill(3, 'قيادة الفرق', 4, 0, 0.81), skill(1, 'إعداد القوائم المالية', 4, 4, 0.69)],
}

const PLAN: DevelopmentPlan = {
  current_title_id: 7,
  target_title_id: 8,
  readiness_score: 42,
  low_evidence: false,
  phases: [
    {
      phase: '30',
      goal_ar: 'بناء الأساس في «قيادة الفرق»',
      actions: [
        { skill_id: 3, type: 'mentoring', title_ar: 'جلسات توجيه في «قيادة الفرق»', effort_hours: 10, success_metric_ar: '٣ جلسات موثّقة' },
      ],
    },
  ],
}

const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status }))

// `me` is the signed-in employee's job_title; null makes the profile request fail.
function stubApi(gap: GapAnalysis | 'fail' = GAP, me: string | null = 'مهندسة طيران', plan: DevelopmentPlan | 'fail' = PLAN) {
  const fetchMock = vi.fn((url: string) => {
    if (url.includes('/api/onboarding/me')) return me === null ? json({}, 500) : json({ job_title: me })
    if (url.includes('/api/career/titles/match')) {
      const jobTitle = new URL(url).searchParams.get('job_title')
      const match = TITLES.find((t) => t.name_ar === jobTitle)
      return match ? json(match) : json({ detail: 'not found' }, 404)
    }
    if (url.includes('/api/career/titles')) return json(TITLES)
    if (url.includes('/api/career/plan')) return plan === 'fail' ? json({}, 500) : json(plan)
    if (gap === 'fail') return Promise.resolve(new Response('', { status: 500 }))
    return Promise.resolve(new Response(JSON.stringify(gap)))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('CareerPage', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('suggests the next title and shows readiness, radar and skill lists', async () => {
    const fetchMock = stubApi()
    const user = userEvent.setup()
    render(<CareerPage />)

    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    expect(screen.getByLabelText('المنصب المستهدف')).toHaveValue('8')

    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))

    expect(await screen.findByRole('img', { name: /رادار الفجوة/ })).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '42')
    expect(screen.getAllByText('قيادة الفرق')).toHaveLength(2) // radar axis + missing list
    expect(screen.getByText(/أولوية عالية/)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('gap-analysis?current_title_id=7&target_title_id=8'))
    expect(await screen.findByText('بناء الأساس في «قيادة الفرق»')).toBeInTheDocument()
    expect(screen.getByText('أول ٣٠ يوم')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'ESCO' })).toHaveAttribute(
      'href',
      'http://data.europa.eu/esco/occupation/30f3ea93-882a-4525-841c-1d5b4b64076f',
    )
    expect(screen.getByText(/10 ساعة/)).toBeInTheDocument()
  })

  it('marks a result built on few postings as a rough estimate', async () => {
    stubApi({ ...GAP, gap: { ...GAP.gap, evidence_postings: 1, low_evidence: true } })
    const user = userEvent.setup()
    render(<CareerPage />)
    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))
    expect(await screen.findByRole('note')).toHaveTextContent('النتيجة تقريبية')
  })

  it('does not warn when there are enough postings', async () => {
    stubApi()
    const user = userEvent.setup()
    render(<CareerPage />)
    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))
    await screen.findByRole('progressbar')
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('says so when there is nothing to learn', async () => {
    stubApi(GAP, 'مهندسة طيران', { ...PLAN, phases: [] })
    const user = userEvent.setup()
    render(<CareerPage />)
    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))
    expect(await screen.findByText(/ما تحتاجين خطة/)).toBeInTheDocument()
  })

  it('keeps the gap result when only the plan fails', async () => {
    stubApi(GAP, 'مهندسة طيران', 'fail')
    const user = userEvent.setup()
    render(<CareerPage />)
    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('ما قدرنا نجهّز الخطة')
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('keeps the button disabled until both titles are chosen', async () => {
    stubApi()
    render(<CareerPage />)
    await screen.findByLabelText('المنصب الحالي')
    expect(screen.getByRole('button', { name: 'حلّلي الفجوة' })).toBeDisabled()
  })

  it('shows an Arabic error when the analysis fails', async () => {
    stubApi('fail')
    const user = userEvent.setup()
    render(<CareerPage />)
    await user.selectOptions(await screen.findByLabelText('المنصب الحالي'), '7')
    await user.click(screen.getByRole('button', { name: 'حلّلي الفجوة' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('صار خطأ في التحليل')
  })

  it('prefills the current and next title from the employee profile', async () => {
    stubApi(GAP, 'محاسب')
    render(<CareerPage />)
    expect(await screen.findByText(/اخترنا منصبك الحالي من ملفك: «محاسب»/)).toBeInTheDocument()
    expect(screen.getByLabelText('المنصب الحالي')).toHaveValue('7')
    expect(screen.getByLabelText('المنصب المستهدف')).toHaveValue('8')
    expect(screen.getByRole('button', { name: 'حلّلي الفجوة' })).toBeEnabled()
  })

  it('asks for a manual choice when the profile title has no postings', async () => {
    stubApi(GAP, 'مهندسة طيران')
    render(<CareerPage />)
    expect(await screen.findByText(/«مهندسة طيران» ما عندنا له إعلانات/)).toBeInTheDocument()
    expect(screen.getByLabelText('المنصب الحالي')).toHaveValue('')
  })

  it('still works by hand when the profile cannot load', async () => {
    stubApi(GAP, null)
    render(<CareerPage />)
    expect(await screen.findByText('ما قدرنا نقرأ ملفك، اختاري منصبك الحالي بنفسك.')).toBeInTheDocument()
    expect(screen.getByLabelText('المنصب الحالي')).toHaveValue('')
  })

  it('shows an error when titles cannot load', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))))
    render(<CareerPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('ما قدرنا نجيب المسميات')
  })
})
