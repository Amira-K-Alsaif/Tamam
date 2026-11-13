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

  it('says the service is busy when the backend answers 503', async () => {
    replyWith(null, 503)
    render(<ChatPage />)

    await ask('كم يوم إجازتي؟')

    expect(await screen.findByRole('alert')).toHaveTextContent('حاول بعد قليل')
  })

  it('tells the user to check the server when it cannot be reached', async () => {
    replyWith(null, 500)
    render(<ChatPage />)

    await ask('كم يوم إجازتي؟')

    expect(await screen.findByRole('alert')).toHaveTextContent('تأكد إنه شغال')
  })

  it('shows the section alone for sources without a page', async () => {
    replyWith({
      answer: 'يومان في الأسبوع [1].',
      found: true,
      sources: [
        {
          document_id: 'remote-work',
          document_title: 'سياسة العمل عن بُعد',
          page: null,
          section_title: 'عدد الأيام',
          quote: 'الحد الأقصى المعتمد يومان في الأسبوع.',
        },
      ],
    })
    render(<ChatPage />)

    await ask('كم يوم أشتغل من البيت؟')

    const sources = await screen.findByRole('complementary', { name: 'مصادر الإجابة' })
    expect(await within(sources).findByText('عدد الأيام')).toBeInTheDocument()
    expect(within(sources).queryByText(/صفحة/)).not.toBeInTheDocument()
  })

  it('fills the question from a suggestion', async () => {
    render(<ChatPage />)

    await userEvent.click(screen.getByRole('button', { name: 'أبي أشتغل من البيت' }))

    expect(screen.getByLabelText('سؤالك')).toHaveValue('أبي أشتغل من البيت')
  })
})
