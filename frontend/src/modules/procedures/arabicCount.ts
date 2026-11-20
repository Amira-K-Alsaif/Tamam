type Forms = { one: string; two: string; few: string; many: string }

/** A count with its noun in correct Arabic agreement: «خطوة واحدة»، «خطوتان»، «3 خطوات»، «11 خطوة». */
export function arabicCount(n: number, forms: Forms): string {
  if (n === 1) return forms.one
  if (n === 2) return forms.two
  const lastTwo = n % 100
  return `${n} ${lastTwo >= 3 && lastTwo <= 10 ? forms.few : forms.many}`
}

export const STEPS: Forms = { one: 'خطوة واحدة', two: 'خطوتان', few: 'خطوات', many: 'خطوة' }
export const FORMS: Forms = { one: 'نموذج واحد', two: 'نموذجان', few: 'نماذج', many: 'نموذجًا' }
export const PROCEDURES: Forms = { one: 'إجراء واحد', two: 'إجراءان', few: 'إجراءات', many: 'إجراءً' }
export const FIELDS: Forms = { one: 'حقل واحد', two: 'حقلان', few: 'حقول', many: 'حقلًا' }
