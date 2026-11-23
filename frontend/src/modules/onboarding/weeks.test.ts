import { describe, expect, it } from 'vitest'
import { taskCount, weekName } from './weeks'

describe('week tabs', () => {
  it('names weeks with words', () => {
    expect(weekName(1)).toBe('الأسبوع الأول')
    expect(weekName(3)).toBe('الأسبوع الثالث')
    expect(weekName(12)).toBe('الأسبوع 12')
  })

  it('counts tasks the way Arabic counts them', () => {
    expect(taskCount(1)).toBe('مهمة وحدة')
    expect(taskCount(2)).toBe('مهمتين')
    expect(taskCount(8)).toBe('8 مهام')
    expect(taskCount(11)).toBe('11 مهمة')
  })
})
