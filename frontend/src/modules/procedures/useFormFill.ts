import { useState } from 'react'
import { getMe, type EmployeeProfile } from '../../lib/api'
import type { CompanyForm, ProfileKey } from './proceduresApi'

const PROFILE_VALUE: Record<ProfileKey, (me: EmployeeProfile) => string> = {
  full_name: (me) => me.full_name,
  employee_id: (me) => me.id,
}

export type FillStatus = { kind: 'idle' } | { kind: 'filling' } | { kind: 'filled'; count: number } | { kind: 'error' }

/** The form's answers, and the action that fills what the employee profile already knows. */
export function useFormFill(form: CompanyForm) {
  const [values, setValues] = useState<Record<string, string>>({})
  // Labels whose value still comes unchanged from the profile, shown as «من ملفك».
  const [fromProfile, setFromProfile] = useState<string[]>([])
  const [status, setStatus] = useState<FillStatus>({ kind: 'idle' })

  const prefillable = form.fields.filter((field) => field.prefill_from !== null)
  const missing = form.fields.filter((field) => !values[field.label]?.trim()).map((field) => field.label)

  function setValue(label: string, value: string) {
    setValues((current) => ({ ...current, [label]: value }))
    setFromProfile((current) => current.filter((l) => l !== label))
  }

  async function fillFromProfile() {
    setStatus({ kind: 'filling' })
    try {
      const me = await getMe()
      const filled: Record<string, string> = {}
      for (const field of prefillable) {
        if (field.prefill_from) filled[field.label] = PROFILE_VALUE[field.prefill_from](me)
      }
      setValues((current) => ({ ...current, ...filled }))
      setFromProfile(Object.keys(filled))
      setStatus({ kind: 'filled', count: Object.keys(filled).length })
    } catch {
      setStatus({ kind: 'error' })
    }
  }

  /** The answers as plain text, one "label: value" line per field, ready to paste. */
  function asText() {
    return [form.title, ...form.fields.map((field) => `${field.label}: ${values[field.label]?.trim() ?? ''}`)].join('\n')
  }

  return {
    values,
    setValue,
    isFromProfile: (label: string) => fromProfile.includes(label),
    canPrefill: prefillable.length > 0,
    status,
    fillFromProfile,
    missing,
    asText,
  }
}
