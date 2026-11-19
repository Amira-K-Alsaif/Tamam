import { useState } from 'react'
import { memberSubtitle } from './labels'
import type { DepartmentDetail } from './orgMapApi'
import { PersonAvatar } from './PersonAvatar'

type DepartmentPanelProps = {
  department: DepartmentDetail
  personId: string | null
  onPerson: (id: string) => void
}

/** The open department: its teams as filters, and the people in it. */
export function DepartmentPanel({ department, personId, onPerson }: DepartmentPanelProps) {
  // Keyed by department, so switching departments clears the team filter.
  const [filter, setFilter] = useState<{ department: string; team: string | null }>({
    department: department.id,
    team: null,
  })
  const team = filter.department === department.id ? filter.team : null
  const members = team ? department.members.filter((m) => m.team === team) : department.members

  function toggleTeam(name: string) {
    setFilter({ department: department.id, team: team === name ? null : name })
  }

  return (
    <section
      aria-label={`أعضاء ${department.name}`}
      className="flex flex-col gap-5 rounded-2xl border border-mint/20 bg-mint/5 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="m-0 font-display text-xl font-semibold">{department.name}</h2>
        <div className="flex flex-wrap gap-2">
          {department.teams.map(({ name, size }) => (
            <button
              key={name}
              type="button"
              aria-pressed={team === name}
              onClick={() => toggleTeam(name)}
              className={`inline-flex h-8 items-center rounded-full border px-3 text-xs ${
                team === name ? 'border-mint bg-mint/10 text-mint' : 'border-line bg-raised text-soft'
              }`}
            >
              {name} · {size}
            </button>
          ))}
        </div>
      </div>

      {members.length === 0 ? (
        <p className="m-0 text-sm text-faint">ما فيه أحد معروض من هذا الفريق حالياً.</p>
      ) : (
        <ul className="m-0 grid list-none gap-3 p-0 sm:grid-cols-2 xl:grid-cols-3">
          {members.map((member) => {
            const open = member.id === personId
            const self = member.relation === 'self'
            return (
              <li key={member.id}>
                <button
                  type="button"
                  aria-pressed={open}
                  onClick={() => onPerson(member.id)}
                  className={`flex w-full items-center gap-3 rounded-2xl border p-3.5 text-start ${
                    open
                      ? 'border-mint/70 bg-mint/10'
                      : self
                        ? 'border-dashed border-mint/50 bg-sunken'
                        : 'border-line bg-sunken hover:border-line-strong'
                  }`}
                >
                  <PersonAvatar person={member} />
                  <span className="flex min-w-0 flex-col leading-normal">
                    <strong className="text-sm">{member.full_name}</strong>
                    <span className={`text-xs ${self ? 'text-mint' : 'text-faint'}`}>
                      {memberSubtitle(member)}
                    </span>
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
