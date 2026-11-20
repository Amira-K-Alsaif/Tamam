import { describe, expect, it } from 'vitest'
import { arabicCount, STEPS } from './arabicCount'

describe('arabicCount', () => {
  it('agrees the noun with the number', () => {
    expect(arabicCount(1, STEPS)).toBe('خطوة واحدة')
    expect(arabicCount(2, STEPS)).toBe('خطوتان')
    expect(arabicCount(3, STEPS)).toBe('3 خطوات')
    expect(arabicCount(10, STEPS)).toBe('10 خطوات')
    expect(arabicCount(11, STEPS)).toBe('11 خطوة')
    expect(arabicCount(103, STEPS)).toBe('103 خطوات')
  })
})
