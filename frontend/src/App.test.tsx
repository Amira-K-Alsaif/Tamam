import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('links every module from the sidebar', () => {
    renderAt('/')
    const nav = screen.getByRole('navigation', { name: 'القائمة الرئيسية' })
    // Home plus the six modules.
    expect(within(nav).getAllByRole('link')).toHaveLength(7)
    expect(within(nav).getByRole('link', { name: 'خريطة الشركة' })).toHaveAttribute('href', '/org-map')
  })

  it('marks the current page in the sidebar', () => {
    renderAt('/career')
    const nav = screen.getByRole('navigation', { name: 'القائمة الرئيسية' })
    expect(within(nav).getByRole('link', { name: 'مساري المهني' })).toHaveAttribute('aria-current', 'page')
    expect(within(nav).getByRole('link', { name: 'الرئيسية' })).not.toHaveAttribute('aria-current')
  })

  it('opens a module page from the home page', async () => {
    renderAt('/')
    const modules = screen.getByRole('list', { name: 'الأقسام' })
    await userEvent.click(within(modules).getByRole('link', { name: /مساري التأهيلي/ }))
    expect(screen.getByRole('heading', { level: 1, name: 'مساري التأهيلي' })).toBeInTheDocument()
  })

  it('sends unknown addresses to the home page', () => {
    renderAt('/does-not-exist')
    expect(screen.getByRole('heading', { level: 1, name: /صباح الخير/ })).toBeInTheDocument()
  })

  it('shows the backend as online when the health check succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ status: 'ok' }), { status: 200 })),
    )
    renderAt('/')
    expect(await screen.findByText('الخادم متصل')).toBeInTheDocument()
  })

  it('shows the backend as offline when the health check fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 500 })))
    renderAt('/')
    expect(await screen.findByText('الخادم غير متصل')).toBeInTheDocument()
  })
})
