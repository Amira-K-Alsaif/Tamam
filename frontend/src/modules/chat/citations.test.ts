import { describe, expect, it } from 'vitest'
import { withoutCitationNumbers } from './citations'

describe('withoutCitationNumbers', () => {
  it('removes the numbers and the space before them', () => {
    expect(withoutCitationNumbers('الحد الأقصى يومان في الأسبوع [1].')).toBe(
      'الحد الأقصى يومان في الأسبوع.',
    )
  })

  it('removes several numbers and keeps the lines of a list', () => {
    expect(withoutCitationNumbers('1. افتح البوابة [1].\n2. اختر النظام [1][2].')).toBe(
      '1. افتح البوابة.\n2. اختر النظام.',
    )
  })

  it('leaves an answer without numbers unchanged', () => {
    expect(withoutCitationNumbers('ما لقيت هذي المعلومة في وثائق الشركة.')).toBe(
      'ما لقيت هذي المعلومة في وثائق الشركة.',
    )
  })
})
