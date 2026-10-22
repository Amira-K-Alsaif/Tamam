import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists all six modules', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    render(<App />)
    expect(screen.getAllByRole('listitem')).toHaveLength(6)
    expect(screen.getByText('مساري المهني')).toBeInTheDocument()
  })

  it('shows the backend as online when the health check succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ status: 'ok' }), { status: 200 })),
    )
    render(<App />)
    expect(await screen.findByText('الخادم متصل')).toBeInTheDocument()
  })

  it('shows the backend as offline when the health check fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 500 })))
    render(<App />)
    expect(await screen.findByText('الخادم غير متصل')).toBeInTheDocument()
  })
})
