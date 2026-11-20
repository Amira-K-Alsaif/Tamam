import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { EmployeeProfile } from '../../lib/api'
import type { CompanyForm } from './proceduresApi'
import ProceduresPage from './ProceduresPage'

const LEAVE_FORM: CompanyForm = {
  id: 'leave-request-form',
  title: 'نموذج طلب إجازة سنوية',
  department: 'الموارد البشرية',
  instructions: 'تُعبأ الحقول في بوابة الموارد البشرية.',
  fields: [
    { label: 'اسم الموظف', kind: 'text', prefill_from: 'full_name' },
    { label: 'الرقم الوظيفي', kind: 'text', prefill_from: 'employee_id' },
    { label: 'تاريخ البداية', kind: 'date', prefill_from: null },
    { label: 'عدد الأيام', kind: 'number', prefill_from: null },
  ],
  source: {
    document_id: 'leave-request-form',
    document_title: 'نموذج طلب إجازة سنوية',
    page: null,
    section_title: 'الحقول',
    quote: 'اسم الموظف، الرقم الوظيفي، تاريخ البداية، عدد الأيام.',
  },
}

const ME: EmployeeProfile = {
  id: 'emp-004',
  full_name: 'نورة العتيبي',
  department_id: 'dep-data',
  team: 'البيانات والتحليلات',
  job_title: 'محللة بيانات',
  manager_id: 'emp-002',
  years_of_experience: 0,
  role: 'employee',
}

type Reply = { status?: number; body?: unknown }

function serve(routes: Record<string, Reply>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input))
      const reply = routes[url.pathname + url.search] ?? { status: 404 }
      return new Response(reply.body === undefined ? '' : JSON.stringify(reply.body), {
        status: reply.status ?? 200,
      })
    }),
  )
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

const FORM_URL = '/procedures?form=leave-request-form'
const FORM_API = '/api/procedures/forms/leave-request-form'

describe('Forms on the procedures page', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('lists the company forms under the catalog', async () => {
    serve({ '/api/procedures': { body: [] }, '/api/procedures/forms': { body: [LEAVE_FORM] } })
    renderAt('/procedures')

    const forms = await screen.findByRole('list', { name: 'النماذج' })
    expect(within(forms).getByRole('link', { name: /نموذج طلب إجازة سنوية/ })).toHaveAttribute(
      'href',
      `/procedures?form=leave-request-form`,
    )
    expect(within(forms).getByText('الموارد البشرية · 4 حقول')).toBeInTheDocument()
  })
})

describe('FormFiller', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('shows every field empty, with the instructions and the source', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM } })
    renderAt(FORM_URL)

    expect(await screen.findByRole('heading', { level: 1, name: LEAVE_FORM.title })).toBeInTheDocument()
    expect(screen.getByLabelText('اسم الموظف')).toHaveValue('')
    expect(screen.getByLabelText('تاريخ البداية')).toHaveAttribute('type', 'date')
    expect(screen.getByLabelText('عدد الأيام')).toHaveAttribute('type', 'number')
    expect(screen.getByText(LEAVE_FORM.instructions as string)).toBeInTheDocument()
    expect(within(screen.getByRole('region', { name: 'مصدر النموذج' })).getByText('الحقول')).toBeInTheDocument()
  })

  it('fills the name and employee number from the profile and marks them', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM }, '/api/onboarding/me': { body: ME } })
    renderAt(FORM_URL)

    await userEvent.click(await screen.findByRole('button', { name: 'عبّي النموذج عني' }))

    expect(await screen.findByText('تعبّى حقلان من ملفك. كمّلي الباقي.')).toBeInTheDocument()
    expect(screen.getByLabelText('اسم الموظف')).toHaveValue('نورة العتيبي')
    expect(screen.getByLabelText('الرقم الوظيفي')).toHaveValue('emp-004')
    expect(screen.getByLabelText('تاريخ البداية')).toHaveValue('')
    expect(screen.getAllByText('من ملفك')).toHaveLength(2)
    expect(screen.getByRole('progressbar', { name: 'عبّيتِ 2 من 4' })).toHaveAttribute('aria-valuenow', '50')
  })

  it('drops the «من ملفك» mark once the employee edits the value', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM }, '/api/onboarding/me': { body: ME } })
    renderAt(FORM_URL)
    await userEvent.click(await screen.findByRole('button', { name: 'عبّي النموذج عني' }))
    await screen.findByText('تعبّى حقلان من ملفك. كمّلي الباقي.')

    await userEvent.type(screen.getByLabelText('اسم الموظف'), ' م')

    expect(screen.getAllByText('من ملفك')).toHaveLength(1)
  })

  it('says what to do when the profile cannot be reached', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM }, '/api/onboarding/me': { status: 503 } })
    renderAt(FORM_URL)

    await userEvent.click(await screen.findByRole('button', { name: 'عبّي النموذج عني' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('عبّي الحقول بنفسك')
  })

  it('lists the missing fields instead of copying an incomplete form', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM }, '/api/onboarding/me': { body: ME } })
    renderAt(FORM_URL)
    await userEvent.click(await screen.findByRole('button', { name: 'عبّي النموذج عني' }))
    await screen.findByText('تعبّى حقلان من ملفك. كمّلي الباقي.')

    await userEvent.click(screen.getByRole('button', { name: 'انسخي النموذج' }))

    expect(screen.getByRole('alert')).toHaveTextContent('باقي تعبّين: تاريخ البداية، عدد الأيام.')
  })

  it('copies the completed form as text', async () => {
    serve({ [FORM_API]: { body: LEAVE_FORM }, '/api/onboarding/me': { body: ME } })
    const user = userEvent.setup()
    const writeText = vi.spyOn(navigator.clipboard, 'writeText')
    renderAt(FORM_URL)
    await user.click(await screen.findByRole('button', { name: 'عبّي النموذج عني' }))
    await screen.findByText('تعبّى حقلان من ملفك. كمّلي الباقي.')
    await user.type(screen.getByLabelText('تاريخ البداية'), '2026-12-01')
    await user.type(screen.getByLabelText('عدد الأيام'), '5')

    await user.click(screen.getByRole('button', { name: 'انسخي النموذج' }))

    expect(await screen.findByText(/نسخنا النموذج/)).toBeInTheDocument()
    expect(writeText).toHaveBeenCalledWith(
      'نموذج طلب إجازة سنوية\nاسم الموظف: نورة العتيبي\nالرقم الوظيفي: emp-004\nتاريخ البداية: 2026-12-01\nعدد الأيام: 5',
    )
  })

  it('says when the form does not exist', async () => {
    serve({})
    renderAt('/procedures?form=nope')

    expect(await screen.findByRole('alert')).toHaveTextContent('ما لقينا هذا النموذج')
  })
})
