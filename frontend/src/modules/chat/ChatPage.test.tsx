import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { AskResponse } from '../../lib/api'
import ChatPage from './ChatPage'

function replyWith(body: AskResponse | null, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(body ? JSON.stringify(body) : '', { status })),
  )
}

async function ask(question: string) {
  await userEvent.type(screen.getByLabelText('سؤالك'), question)
  await userEvent.click(screen.getByRole('button', { name: 'إرسال' }))
}

describe('ChatPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the answer and its sources', async () => {
    replyWith({
      answer: 'إجازتك ٢١ يوماً [1].',
      found: true,
      sources: [
        {
          document_id: 'doc-leave',
          document_title: 'سياسة الإجازات',
          page: 4,
          section_title: 'الإجازة السنوية',
          quote: 'يحق للموظف إجازة سنوية مدتها ٢١ يوماً.',
        },
      ],
    })
    render(<ChatPage />)

    await ask('كم يوم إجازتي؟')

    expect(await screen.findByText('إجازتك ٢١ يوماً [1].')).toBeInTheDocument()
    const sources = screen.getByRole('complementary', { name: 'مصادر الإجابة' })
    expect(within(sources).getByText('[1] سياسة الإجازات')).toBeInTheDocument()
    expect(within(sources).getByText('صفحة 4 · الإجازة السنوية')).toBeInTheDocument()
  })

  it('shows "not found" without sources', async () => {
    replyWith({ answer: 'ما لقيت هذي المعلومة في وثائق الشركة.', found: false, sources: [] })
    render(<ChatPage />)

    await ask('كم بدل السكن؟')

    expect(await screen.findByText('ما لقيت هذي المعلومة في وثائق الشركة.')).toBeInTheDocument()
    expect(screen.getByText('بتظهر هنا مصادر آخر إجابة.')).toBeInTheDocument()
  })

  it('tells the user what to do when the backend fails', async () => {
    replyWith(null, 503)
    render(<ChatPage />)

    await ask('كم يوم إجازتي؟')

    expect(await screen.findByRole('alert')).toHaveTextContent('حاول مرة ثانية')
  })

  it('fills the question from a suggestion', async () => {
    render(<ChatPage />)

    await userEvent.click(screen.getByRole('button', { name: 'أبي أشتغل من البيت' }))

    expect(screen.getByLabelText('سؤالك')).toHaveValue('أبي أشتغل من البيت')
  })
})
