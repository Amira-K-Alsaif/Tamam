import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import OrgMapPage from './OrgMapPage'
import type { DepartmentDetail, OrgOverview, PersonDetail, PersonSummary, SearchResponse } from './orgMapApi'

function summary(id: string, full_name: string, extra: Partial<PersonSummary> = {}): PersonSummary {
  return {
    id,
    full_name,
    gender: 'f',
    job_title: 'محللة بيانات',
    department_id: 'analytics',
    team: 'فريق التحليلات',
    is_department_head: false,
    relation: null,
    ...extra,
  }
}

const reem = summary('emp-201', 'ريم الحربي', {
  job_title: 'مديرة البيانات والتحليلات',
  is_department_head: true,
  relation: 'manager',
})
const fahad = summary('emp-202', 'فهد العنزي', { gender: 'm', job_title: 'مسؤول حوكمة البيانات', team: 'الحوكمة' })
const noura = summary('emp-004', 'نورة العتيبي', { relation: 'self' })

const OVERVIEW: OrgOverview = {
  company_name: 'نخلة للتقنية',
  employee_count: 32,
  ceo: summary('emp-101', 'خالد السبيعي', { gender: 'm', job_title: 'الرئيس التنفيذي' }),
  departments: [
    { id: 'hr', name: 'الموارد البشرية', head: summary('emp-301', 'سارة القحطاني'), headcount: 14, is_mine: false },
    { id: 'analytics', name: 'البيانات والتحليلات', head: reem, headcount: 18, is_mine: true },
  ],
  my_department_id: 'analytics',
  my_manager_id: 'emp-201',
}

const ANALYTICS: DepartmentDetail = {
  id: 'analytics',
  name: 'البيانات والتحليلات',
  headcount: 18,
  teams: [
    { name: 'فريق التحليلات', size: 8 },
    { name: 'الحوكمة', size: 3 },
  ],
  members: [reem, fahad, noura],
}

function detail(person: PersonSummary, extra: Partial<PersonDetail> = {}): PersonDetail {
  return {
    ...person,
    department_name: 'البيانات والتحليلات',
    email: 'someone@nakhla.example',
    office: 'الدور 4',
    contact_topics: [],
    procedures: [],
    ...extra,
  }
}

const PEOPLE: Record<string, PersonDetail> = {
  'emp-201': detail(reem, {
    contact_topics: ['اعتماد الإجازات', 'موافقة الصلاحيات'],
    procedures: [{ id: 'warehouse', title: 'صلاحية بيانات المستودع' }],
  }),
  'emp-202': detail(fahad, { contact_topics: ['حوكمة البيانات'] }),
}

const SEARCH: SearchResponse = {
  query: 'صلاحيات البيانات',
  hits: [{ person: fahad, department_name: 'البيانات والتحليلات', matched_topic: 'حوكمة البيانات' }],
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

function backend({ overviewStatus = 200 } = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      const url = new URL(input)
      const path = url.pathname
      if (path.endsWith('/overview')) return json(OVERVIEW, overviewStatus)
      if (path.endsWith('/departments/analytics')) return json(ANALYTICS)
      if (path.endsWith('/search')) return json(SEARCH)
      const person = PEOPLE[path.split('/').pop() ?? '']
      return person ? json(person) : json({}, 404)
    }),
  )
}

function renderPage() {
  render(
    <MemoryRouter>
      <OrgMapPage />
    </MemoryRouter>,
  )
}

describe('OrgMapPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('opens the viewer’s department and manager', async () => {
    backend()
    renderPage()

    expect(await screen.findByRole('button', { name: /خالد السبيعي/ })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /البيانات والتحليلات/, pressed: true })).toHaveTextContent('قسمك · 18 موظف')

    const panel = await screen.findByRole('complementary', { name: 'بطاقة الشخص' })
    expect(await within(panel).findByText('مديرتك المباشرة')).toBeInTheDocument()
    expect(within(panel).getByText('كلّميها عن')).toBeInTheDocument()
    expect(within(panel).getByText('موافقة الصلاحيات')).toBeInTheDocument()
    expect(within(panel).getByRole('link', { name: 'صلاحية بيانات المستودع' })).toBeInTheDocument()
  })

  it('marks the viewer and filters members by team', async () => {
    backend()
    renderPage()

    const members = await screen.findByRole('region', { name: 'أعضاء البيانات والتحليلات' })
    expect(within(members).getByText('أنت · محللة بيانات')).toBeInTheDocument()

    await userEvent.click(within(members).getByRole('button', { name: 'الحوكمة · 3' }))

    expect(within(members).getByText('فهد العنزي')).toBeInTheDocument()
    expect(within(members).queryByText('نورة العتيبي')).not.toBeInTheDocument()
  })

  it('answers who to talk to and opens the person', async () => {
    backend()
    renderPage()
    await screen.findByRole('region', { name: 'أعضاء البيانات والتحليلات' })

    await userEvent.type(screen.getByLabelText('ابحث عن شخص حسب الموضوع'), 'صلاحيات البيانات')
    await userEvent.click(screen.getByRole('button', { name: 'بحث' }))

    const results = await screen.findByRole('region', { name: 'نتائج البحث' })
    await userEvent.click(within(results).getByRole('button', { name: /فهد العنزي/ }))

    const panel = screen.getByRole('complementary', { name: 'بطاقة الشخص' })
    expect(await within(panel).findByText('كلّميه عن')).toBeInTheDocument()
  })

  it('tells the user what to do when the backend fails', async () => {
    backend({ overviewStatus: 503 })
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('تأكد إن الخادم شغال')
    expect(screen.getByRole('button', { name: 'حاول مرة ثانية' })).toBeInTheDocument()
  })
})
