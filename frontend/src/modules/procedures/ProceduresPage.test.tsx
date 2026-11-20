import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Procedure } from './proceduresApi'
import ProceduresPage from './ProceduresPage'

const VPN: Procedure = {
  id: 'proc-vpn',
  title: 'دليل تفعيل الاتصال الآمن VPN',
  department: 'تقنية المعلومات',
  summary: 'طلب صلاحية VPN وتفعيلها على جهاز العمل.',
  owner: 'مكتب الدعم التقني',
  duration_text: 'يوم عمل واحد',
  requirements: ['جهاز عمل مسجّل', 'تفعيل التحقق الثنائي'],
  forms: ['نموذج طلب صلاحية'],
  steps: [
    { order: 2, title: 'ثبّت التطبيق', detail: 'ثبّت تطبيق VPN من بوابة البرامج.' },
    { order: 1, title: 'ارفع الطلب', detail: 'ارفع طلب صلاحية VPN من بوابة الخدمات.' },
  ],
  source: {
    document_id: 'vpn',
    document_title: 'دليل الاتصال الآمن',
    page: 2,
    section_title: 'الخطوات',
    quote: 'ارفع طلب صلاحية VPN من بوابة الخدمات.',
  },
}

const REIMBURSEMENT: Procedure = {
  ...VPN,
  id: 'proc-reimbursements',
  title: 'إجراء تعويض مصاريف العمل',
  department: 'المالية',
  summary: 'تعويض المصروفات الموافق عليها.',
  forms: [],
}

type Reply = { status?: number; body?: unknown }

/** Answers each backend URL from `routes`, matched by its path and query. */
function serve(routes: Record<string, Reply>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = new URL(String(input))
    const reply = { '/api/procedures/forms': { body: [] }, ...routes }[url.pathname + url.search] ?? { status: 404 }
    return new Response(reply.body === undefined ? '' : JSON.stringify(reply.body), {
      status: reply.status ?? 200,
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/procedures" element={<ProceduresPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProceduresPage catalog', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('lists every procedure with its department and step count', async () => {
    serve({ '/api/procedures': { body: [VPN, REIMBURSEMENT] } })
    renderAt('/procedures')

    const list = await screen.findByRole('list', { name: 'الإجراءات' })
    expect(within(list).getByRole('link', { name: /دليل تفعيل الاتصال الآمن VPN/ })).toHaveAttribute(
      'href',
      '/procedures?id=proc-vpn',
    )
    expect(within(list).getAllByText('خطوتان')).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'المالية' })).toBeInTheDocument()
  })

  it('sends the search text to the backend', async () => {
    const fetchMock = serve({
      '/api/procedures': { body: [VPN, REIMBURSEMENT] },
      '/api/procedures?q=%D8%AA%D8%B9%D9%88%D9%8A%D8%B6': { body: [REIMBURSEMENT] },
    })
    renderAt('/procedures')
    await screen.findByRole('list', { name: 'الإجراءات' })

    await userEvent.type(screen.getByLabelText('ابحث عن إجراء'), 'تعويض')

    expect(await screen.findByText('إجراء واحد')).toBeInTheDocument()
    expect(screen.queryByText(VPN.title)).not.toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('?q=%D8%AA'))
  })

  it('filters by department', async () => {
    serve({
      '/api/procedures': { body: [VPN, REIMBURSEMENT] },
      '/api/procedures?department=%D8%A7%D9%84%D9%85%D8%A7%D9%84%D9%8A%D8%A9': { body: [REIMBURSEMENT] },
    })
    renderAt('/procedures')

    await userEvent.click(await screen.findByRole('button', { name: 'المالية' }))

    expect(await screen.findByText('إجراء واحد')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'المالية' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('says when nothing matches the search', async () => {
    serve({
      '/api/procedures': { body: [VPN] },
      '/api/procedures?q=xyz': { body: [] },
    })
    renderAt('/procedures')
    await screen.findByRole('list', { name: 'الإجراءات' })

    await userEvent.type(screen.getByLabelText('ابحث عن إجراء'), 'xyz')

    expect(await screen.findByText('ما لقينا إجراء يطابق بحثك.')).toBeInTheDocument()
  })

  it('explains an empty catalog', async () => {
    serve({ '/api/procedures': { body: [] } })
    renderAt('/procedures')

    expect(await screen.findByText('ما فيه إجراءات بعد.')).toBeInTheDocument()
  })

  it('tells the user what to do when the backend fails', async () => {
    serve({ '/api/procedures': { status: 503 } })
    renderAt('/procedures')

    expect(await screen.findByRole('alert')).toHaveTextContent('حاولي مرة ثانية')
  })
})

describe('ProceduresPage detail', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('shows the steps in order, requirements, forms, and the source', async () => {
    serve({ '/api/procedures/proc-vpn': { body: VPN } })
    renderAt('/procedures?id=proc-vpn')

    expect(await screen.findByRole('heading', { level: 1, name: VPN.title })).toBeInTheDocument()
    const steps = within(screen.getByRole('list', { name: 'خطوات الإجراء' })).getAllByRole('listitem')
    expect(steps[0]).toHaveTextContent('ارفع الطلب')
    expect(steps[1]).toHaveTextContent('ثبّت التطبيق')
    expect(steps[0]).toHaveAttribute('aria-current', 'step')

    expect(screen.getByLabelText('جهاز عمل مسجّل')).not.toBeChecked()
    expect(screen.getByText('نموذج طلب صلاحية')).toBeInTheDocument()
    const source = screen.getByRole('region', { name: 'مصدر الإجراء' })
    expect(within(source).getByText('صفحة 2 · الخطوات')).toBeInTheDocument()
  })

  it('moves to the next step and celebrates when all are done', async () => {
    serve({ '/api/procedures/proc-vpn': { body: VPN } })
    renderAt('/procedures?id=proc-vpn')
    await screen.findByRole('list', { name: 'خطوات الإجراء' })

    await userEvent.click(screen.getByRole('button', { name: 'تمّت، التالي' }))

    const steps = within(screen.getByRole('list', { name: 'خطوات الإجراء' })).getAllByRole('listitem')
    expect(steps[1]).toHaveAttribute('aria-current', 'step')
    expect(screen.getByLabelText('تمّت الخطوة 1')).toBeChecked()
    expect(screen.getByRole('progressbar', { name: 'أنجزتِ 1 من 2 خطوات' })).toHaveAttribute('aria-valuenow', '50')

    await userEvent.click(screen.getByRole('button', { name: 'تمّت، آخر خطوة' }))

    expect(screen.getByText('تمّ! خلّصتي كل خطوات الإجراء.')).toBeInTheDocument()
  })

  it('remembers ticked items when the procedure is opened again', async () => {
    serve({ '/api/procedures/proc-vpn': { body: VPN } })
    renderAt('/procedures?id=proc-vpn')
    await userEvent.click(await screen.findByLabelText('جهاز عمل مسجّل'))
    expect(screen.getByText('جاهز 1 من 2')).toBeInTheDocument()
    cleanup()

    renderAt('/procedures?id=proc-vpn')

    expect(await screen.findByLabelText('جهاز عمل مسجّل')).toBeChecked()
  })

  it('says when the procedure does not exist', async () => {
    serve({})
    renderAt('/procedures?id=proc-missing')

    expect(await screen.findByRole('alert')).toHaveTextContent('ما لقينا هذا الإجراء')
    expect(screen.getByRole('link', { name: 'كل الإجراءات' })).toHaveAttribute('href', '/procedures')
  })
})
