import type { ReactNode } from 'react'
import type { OrgOverview } from './orgMapApi'
import { PersonAvatar } from './PersonAvatar'

type OrgChartProps = {
  overview: OrgOverview
  departmentId: string | null
  onDepartment: (id: string) => void
  onPerson: (id: string) => void
  children: ReactNode
}

/** The CEO, the departments under them, and the open department below. */
export function OrgChart({ overview, departmentId, onDepartment, onPerson, children }: OrgChartProps) {
  const { ceo, departments } = overview
  const last = departments.length - 1

  return (
    <section
      aria-label="الهيكل التنظيمي"
      className="main-column flex min-w-0 flex-col gap-6 rounded-3xl border border-line bg-surface p-5 sm:p-7"
    >
      {/* No gap here, so the connector lines meet. */}
      <div className="flex flex-col gap-3 lg:gap-0">
        <div className="flex flex-col items-center">
          <button
            type="button"
            onClick={() => onPerson(ceo.id)}
            className="flex items-center gap-3 rounded-2xl border border-line-strong bg-raised px-5 py-3 text-start"
          >
            <PersonAvatar person={ceo} />
            <span className="flex flex-col leading-normal">
              <strong className="text-sm">{ceo.full_name}</strong>
              <span className="text-xs text-faint">{ceo.job_title}</span>
            </span>
          </button>
          <span aria-hidden className="hidden h-6 w-px bg-line-strong lg:block" />
        </div>

        <ul className="m-0 grid list-none grid-cols-2 gap-y-3 p-0 sm:grid-cols-3 lg:grid-cols-5 lg:gap-y-0">
          {departments.map((department, index) => {
            const open = department.id === departmentId
            return (
              <li key={department.id} className="relative flex flex-col px-1.5 lg:pt-6">
                {/* Connector to the CEO: a horizontal run that stops at the outer cards' centres. */}
                <span
                  aria-hidden
                  className={`absolute top-0 hidden h-px bg-line-strong lg:block ${
                    index === 0 ? 'start-1/2 end-0' : index === last ? 'start-0 end-1/2' : 'inset-x-0'
                  }`}
                />
                <span aria-hidden className="absolute start-1/2 top-0 hidden h-6 w-px bg-line-strong lg:block" />
                <button
                  type="button"
                  aria-pressed={open}
                  onClick={() => onDepartment(department.id)}
                  className={`flex h-full flex-col gap-1 rounded-2xl border p-4 text-start ${
                    open ? 'border-mint bg-mint/5' : 'border-line bg-sunken hover:border-line-strong'
                  }`}
                >
                  <strong className="text-sm">{department.name}</strong>
                  <span className={`text-xs ${department.is_mine ? 'text-mint' : 'text-faint'}`}>
                    {department.is_mine ? 'قسمك' : department.head.full_name} · {department.headcount} موظف
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      {children}
    </section>
  )
}
