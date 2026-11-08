import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { GapAnalysis, JobTitle } from './api'
import CareerPage from './CareerPage'

const TITLES: JobTitle[] = [
  { id: 7, code: 'FIN-1', ladder: 'finance', level: 'mid', name_ar: 'محاسب', name_en: 'Accountant', next_title_id: 8, postings_count: 19 },
  { id: 8, code: 'FIN-2', ladder: 'finance', level: 'manager', name_ar: 'مدير مالي', name_en: 'Finance Manager', next_title_id: null, postings_count: 16 },
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
  },
  radar: [skill(2, 'إعداد الموازنات', 4, 2, 0.94), skill(3, 'قيادة الفرق', 4, 0, 0.81), skill(1, 'إعداد القوائم المالية', 4, 4, 0.69)],
}

function stubApi(gap: GapAnalysis | 'fail' = GAP) {
  const fetchMock = vi.fn((url: string) => {
    if (url.includes('/api/career/titles')) return Promise.resolve(new Response(JSON.stringify(TITLES)))
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
    expect(fetchMock).toHaveBeenLastCalledWith(expect.stringContaining('current_title_id=7&target_title_id=8'))
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

  it('shows an error when titles cannot load', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))))
    render(<CareerPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('ما قدرنا نجيب المسميات')
  })
})
