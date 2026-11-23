import { ArrowLeft, MessageCircle, Minus, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

import { coachReply } from '../../lib/api'
import type { CoachMessage, CoachReply } from '../../lib/api'

// What the chat shows: the conversation, plus notes where the coach changed the level.
// Only the conversation goes back to the server.
type ChatEntry = CoachMessage | { role: 'note'; text: string }

// The conversation is kept in this browser, per employee and skill, so it can be reopened.
// The server never stores it. Storage can be unavailable (private mode), so every access is guarded.
function storageKey(employeeId: string, skillId: number) {
  return `tamam.coach.${employeeId}.${skillId}`
}

function loadConversation(employeeId: string, skillId: number): ChatEntry[] {
  try {
    const saved = window.localStorage.getItem(storageKey(employeeId, skillId))
    return saved ? (JSON.parse(saved) as ChatEntry[]) : []
  } catch {
    return []
  }
}

function saveConversation(employeeId: string, skillId: number, messages: ChatEntry[]) {
  try {
    window.localStorage.setItem(storageKey(employeeId, skillId), JSON.stringify(messages))
  } catch {
    // Not saved: the conversation still works, it just will not be there next time.
  }
}

type SkillCoachProps = {
  skillId: number
  skillName: string
  employeeId: string
  onLevelChanged: () => void
  onClose: () => void
}

function conversationOf(entries: ChatEntry[]): CoachMessage[] {
  return entries.filter((entry): entry is CoachMessage => entry.role !== 'note')
}

function levelNote(skillName: string, change: NonNullable<CoachReply['level_change']>): string {
  const direction = change.level > change.previous_level ? 'تحسّن' : 'تغيّر'
  const reached = change.needed_level !== null && change.level >= change.needed_level
  return `${direction} مستواك في ${skillName}: من ${change.previous_level} إلى ${change.level} من 4${
    reached ? '، ووصلتي للمستوى المطلوب' : change.needed_level !== null ? `، والمطلوب ${change.needed_level}` : ''
  }`
}

// A chat window over the page: Tamam coaches one skill, one short idea and question at a time.
// The coach follows the level from the answers and says when it changes; the path follows it.
export function SkillCoach({ skillId, skillName, employeeId, onLevelChanged, onClose }: SkillCoachProps) {
  const [messages, setMessages] = useState<ChatEntry[]>(() => loadConversation(employeeId, skillId))
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(false)
  const [failed, setFailed] = useState(false)
  const [minimised, setMinimised] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)
  // Whether the window opened on a saved conversation; the parent remounts it per skill.
  const resumed = useRef(messages.length > 0)

  async function send(next: ChatEntry[]) {
    setMessages(next)
    setWaiting(true)
    setFailed(false)
    try {
      const reply = await coachReply(skillId, conversationOf(next), employeeId)
      const withReply: ChatEntry[] = [...next, { role: 'coach', text: reply.text }]
      if (reply.level_change) {
        withReply.push({ role: 'note', text: levelNote(skillName, reply.level_change) })
        onLevelChanged()
      }
      setMessages(withReply)
      saveConversation(employeeId, skillId, withReply)
    } catch {
      setFailed(true)
    } finally {
      setWaiting(false)
    }
  }

  // A new conversation starts with the coach; a saved one carries on where it stopped.
  useEffect(() => {
    if (resumed.current) return
    let cancelled = false
    setWaiting(true)
    coachReply(skillId, [], employeeId)
      .then((reply) => {
        if (cancelled) return
        const opening: ChatEntry[] = [{ role: 'coach', text: reply.text }]
        setMessages(opening)
        saveConversation(employeeId, skillId, opening)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
      .finally(() => {
        if (!cancelled) setWaiting(false)
      })
    return () => {
      cancelled = true
    }
  }, [skillId, employeeId])

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: 'end' })
  }, [messages, waiting])

  function submit(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || waiting) return
    setDraft('')
    void send([...messages, { role: 'employee', text }])
  }

  if (minimised) {
    return (
      <button
        type="button"
        onClick={() => setMinimised(false)}
        className="fixed bottom-6 end-6 z-50 flex cursor-pointer items-center gap-2 rounded-full bg-aurora px-5 py-3 font-body font-semibold text-night shadow-lg"
      >
        <MessageCircle aria-hidden className="size-5" />
        رجوع للتدريب: {skillName}
      </button>
    )
  }

  return (
    <section
      role="dialog"
      aria-label={`تدريب مع تمّام: ${skillName}`}
      className="fixed inset-x-4 bottom-4 z-50 flex h-120 max-h-svh flex-col overflow-hidden rounded-3xl border border-line-strong bg-surface shadow-2xl sm:inset-x-auto sm:end-6 sm:bottom-6 sm:w-96"
    >
      <header className="flex items-center gap-3 border-b border-line px-4 py-3">
        <span aria-hidden="true" className="size-8 shrink-0 rounded-full bg-aurora" />
        <div className="flex min-w-0 flex-1 flex-col">
          <strong className="truncate text-sm">مدرّبك في {skillName}</strong>
          <span className="text-xs text-faint">{waiting ? 'تمّام يكتب…' : 'تمّام'}</span>
        </div>
        <button
          type="button"
          aria-label="تصغير"
          onClick={() => setMinimised(true)}
          className="flex size-8 cursor-pointer items-center justify-center rounded-full text-muted hover:bg-white/5"
        >
          <Minus aria-hidden className="size-4" />
        </button>
        <button
          type="button"
          aria-label="إغلاق"
          onClick={onClose}
          className="flex size-8 cursor-pointer items-center justify-center rounded-full text-muted hover:bg-white/5"
        >
          <X aria-hidden className="size-4" />
        </button>
      </header>

      <div className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-4 py-3">
        <ol aria-label="المحادثة" className="m-0 flex list-none flex-col gap-2.5 p-0">
          {messages.map((message, index) =>
            message.role === 'note' ? (
              <li
                key={index}
                role="status"
                className="self-center rounded-full border border-mint/35 px-3 py-1 text-center text-xs text-mint"
              >
                ✓ {message.text}
              </li>
            ) : (
              <li
                key={index}
                className={`max-w-4/5 whitespace-pre-line rounded-2xl px-3.5 py-2 text-sm leading-relaxed ${
                  message.role === 'coach' ? 'self-start rounded-ss-md bg-raised' : 'self-end rounded-se-md bg-mint/15'
                }`}
              >
                {message.text}
              </li>
            ),
          )}
        </ol>
        {waiting && (
          <p role="status" className="m-0 self-start rounded-2xl bg-raised px-3.5 py-2 text-sm text-muted">
            …
          </p>
        )}
        {failed && (
          <p role="alert" className="m-0 text-sm text-warning">
            تمّام ما رد. حاولي مرة ثانية بعد شوي.
          </p>
        )}
        <div ref={bottom} />
      </div>

      <div className="flex flex-col gap-2 border-t border-line px-3 py-3">
        <form
          onSubmit={submit}
          className="flex items-center gap-2 rounded-full border border-mint/35 bg-sunken ps-4 pe-1.5 focus-within:border-mint"
        >
          <label htmlFor={`coach-answer-${skillId}`} className="sr-only">
            جوابك
          </label>
          <input
            id={`coach-answer-${skillId}`}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            maxLength={2000}
            placeholder="اكتبي جوابك…"
            className="min-w-0 flex-1 bg-transparent py-2.5 text-sm text-ink outline-none"
          />
          <button
            type="submit"
            aria-label="أرسلي"
            disabled={!draft.trim() || waiting}
            className="flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-full bg-aurora text-night disabled:opacity-50"
          >
            {/* Points left: "forward" in a right-to-left layout. */}
            <ArrowLeft aria-hidden className="size-4" />
          </button>
        </form>
      </div>
    </section>
  )
}
