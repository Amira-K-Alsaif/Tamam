import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProgressBar } from './ProgressBar'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('uses the default Arabic label for each status', () => {
    render(<StatusBadge status="missing" />)
    expect(screen.getByText('ناقص')).toBeInTheDocument()
  })

  it('accepts a custom label', () => {
    render(<StatusBadge status="done" label="مفعّلة" />)
    expect(screen.getByText('مفعّلة')).toBeInTheDocument()
  })
})

describe('ProgressBar', () => {
  it('exposes its value to assistive technology', () => {
    render(<ProgressBar label="تقدّم المسار" value={62} />)
    const bar = screen.getByRole('progressbar', { name: 'تقدّم المسار' })
    expect(bar).toHaveAttribute('aria-valuenow', '62')
  })

  it('keeps the value between 0 and 100', () => {
    render(<ProgressBar label="الجاهزية" value={140} />)
    expect(screen.getByRole('progressbar', { name: 'الجاهزية' })).toHaveAttribute('aria-valuenow', '100')
  })
})
