import type { PersonSummary } from './orgMapApi'

/** The badge under a person's name: «مديرتك المباشرة», «زميلك المرشد», … */
export function relationLabel(person: PersonSummary): string | null {
  const female = person.gender === 'f'
  switch (person.relation) {
    case 'self':
      return 'أنت'
    case 'manager':
      return female ? 'مديرتك المباشرة' : 'مديرك المباشر'
    case 'mentor':
      return female ? 'زميلتك المرشدة' : 'زميلك المرشد'
    default:
      return null
  }
}

/** The short form used on member cards: «مديرة القسم · مديرتك». */
export function memberSubtitle(person: PersonSummary): string {
  const female = person.gender === 'f'
  const role = person.is_department_head ? (female ? 'مديرة القسم' : 'مدير القسم') : person.job_title
  switch (person.relation) {
    case 'self':
      return `أنت · ${role}`
    case 'manager':
      return `${role} · ${female ? 'مديرتك' : 'مديرك'}`
    case 'mentor':
      return `${role} · ${female ? 'زميلتك المرشدة' : 'زميلك المرشد'}`
    default:
      return role
  }
}

export function contactHeading(person: PersonSummary): string {
  return person.gender === 'f' ? 'كلّميها عن' : 'كلّميه عن'
}

export function proceduresHeading(person: PersonSummary): string {
  return person.gender === 'f' ? 'تعتمد هذي الإجراءات' : 'يعتمد هذي الإجراءات'
}
