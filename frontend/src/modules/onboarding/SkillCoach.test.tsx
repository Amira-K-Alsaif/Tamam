import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SkillCoach } from './SkillCoach'

// The coach replies with how many messages it received; after the third answer it raises the level.
function serve(coachStatus = 200) {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    const sent = JSON.parse(String(init?.body)).messages
    const answers = sent.filter((m: { role: string }) => m.role === 'employee').length
    const level_change = answers === 3 ? { previous_level: 1, level: 2, needed_level: 4 } : null
    return new Response(JSON.stringify({ text: `رد المدرّب ${sent.length}`, level_change }), { status: coachStatus })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderCoach(props: { onLevelChanged?: () => void; onClose?: () => void } = {}) {
  const onLevelChanged = props.onLevelChanged ?? vi.fn()
  const onClose = props.onClose ?? vi.fn()
  render(
    <SkillCoach
      skillId={7}
      skillName="تحليل البيانات"
      employeeId="emp-004"
      onLevelChanged={onLevelChanged}
      onClose={onClose}
    />,
  )
  return { onLevelChanged, onClose }
}

async function answer(text: string) {
  await userEvent.type(screen.getByLabelText('جوابك'), text)
  await userEvent.click(screen.getByRole('button', { name: 'أرسلي' }))
}

beforeEach(() => window.localStorage.clear())

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('SkillCoach', () => {
  it('opens as a chat window with the coach speaking first, then replies to each answer', async () => {
    const fetchMock = serve()
    renderCoach()

    expect(screen.getByRole('dialog', { name: 'تدريب مع تمّام: تحليل البيانات' })).toBeInTheDocument()
    expect(await screen.findByText('رد المدرّب 0')).toBeInTheDocument()
    await answer('جوابي')

    expect(await screen.findByText('رد المدرّب 2')).toBeInTheDocument()
    const lastBody = JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body))
    expect(lastBody.messages.at(-1)).toEqual({ role: 'employee', text: 'جوابي' })
  })

  it('picks up a saved conversation instead of starting again', async () => {
    const fetchMock = serve()
    renderCoach()
    await screen.findByText('رد المدرّب 0')
    await answer('جوابي')
    await screen.findByText('رد المدرّب 2')
    cleanup()
    fetchMock.mockClear()

    renderCoach()

    expect(screen.getByText('جوابي')).toBeInTheDocument()
    expect(screen.getByText('رد المدرّب 2')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('minimises to a button and comes back', async () => {
    serve()
    const { onClose } = renderCoach()
    await screen.findByText('رد المدرّب 0')

    await userEvent.click(screen.getByRole('button', { name: 'تصغير' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'رجوع للتدريب: تحليل البيانات' }))

    expect(screen.getByText('رد المدرّب 0')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'إغلاق' }))
    expect(onClose).toHaveBeenCalled()
  })

  it('shows the level change inside the chat and updates the path, with no button to press', async () => {
    const fetchMock = serve()
    const { onLevelChanged } = renderCoach()
    await screen.findByText('رد المدرّب 0')

    for (const [index, text] of ['أول', 'ثاني', 'ثالث'].entries()) {
      await answer(text)
      // Each answer sends the whole conversation: the coach's reply counts what it received.
      await screen.findByText(`رد المدرّب ${2 * (index + 1)}`)
    }

    expect(screen.getByText('✓ تحسّن مستواك في تحليل البيانات: من 1 إلى 2 من 4، والمطلوب 4')).toBeInTheDocument()
    expect(onLevelChanged).toHaveBeenCalledTimes(1)
    expect(screen.queryByRole('button', { name: 'قيّمي مستواي' })).not.toBeInTheDocument()

    // The note is for the employee only; the coach receives the conversation without it.
    await answer('رابع')
    await screen.findByText('رد المدرّب 8')
    const lastBody = JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body))
    expect(lastBody.messages.every((m: { role: string }) => m.role !== 'note')).toBe(true)
  })

  it('says so when the coach does not answer', async () => {
    serve(503)
    renderCoach()

    expect(await screen.findByRole('alert')).toHaveTextContent('تمّام ما رد')
  })
})
