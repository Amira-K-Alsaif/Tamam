import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { Button } from '../../components/Button'
import { checkSkillLevel, coachReply } from '../../lib/api'
import type { CoachMessage, LevelCheck } from '../../lib/api'

// Answers needed before the level can be checked; matches coach.MIN_ANSWERS on the server.
const MIN_ANSWERS = 3

// A short conversation with Tamam about one skill: an idea, a question, feedback on the answer.
// After a few answers the employee can ask for their level, which updates their path.
export function SkillCoach({
  skillId,
  skillName,
  employeeId,
  onLevelChanged,
}: {
  skillId: number
  skillName: string
  employeeId: string
  onLevelChanged: () => void
}) {
  const [messages, setMessages] = useState<CoachMessage[]>([])
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(true)
  const [failed, setFailed] = useState(false)
  const [check, setCheck] = useState<LevelCheck | null>(null)
  const [checking, setChecking] = useState(false)

  async function send(next: CoachMessage[]) {
    setMessages(next)
    setWaiting(true)
    setFailed(false)
    try {
      const reply = await coachReply(skillId, next, employeeId)
      setMessages([...next, { role: 'coach', text: reply.text }])
    } catch {
      setFailed(true)
    } finally {
      setWaiting(false)
    }
  }

  // The coach speaks first.
  useEffect(() => {
    let cancelled = false
    coachReply(skillId, [], employeeId)
      .then((reply) => {
        if (!cancelled) setMessages([{ role: 'coach', text: reply.text }])
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

  function submit(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || waiting) return
    setDraft('')
    void send([...messages, { role: 'employee', text }])
  }

  async function checkLevel() {
    setChecking(true)
    setFailed(false)
    try {
      setCheck(await checkSkillLevel(skillId, messages, employeeId))
    } catch {
      setFailed(true)
    } finally {
      setChecking(false)
    }
  }

  const answers = messages.filter((message) => message.role === 'employee').length

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-line bg-sunken p-4">
      <p className="m-0 text-sm text-faint">تدريب مع تمّام على «{skillName}»</p>
      <ol aria-label="المحادثة" className="m-0 flex list-none flex-col gap-3 p-0">
        {messages.map((message, index) => (
          <li
            key={index}
            className={`max-w-xl whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              message.role === 'coach' ? 'self-start bg-raised' : 'self-end bg-mint/12 text-ink'
            }`}
          >
            {message.text}
          </li>
        ))}
      </ol>
      {waiting && (
        <p role="status" className="m-0 text-sm text-muted">
          تمّام يكتب…
        </p>
      )}
      {failed && (
        <p role="alert" className="m-0 text-sm text-warning">
          تمّام ما رد. حاولي مرة ثانية بعد شوي.
        </p>
      )}

      {check ? (
        <div role="status" className="flex flex-col gap-2 rounded-2xl border border-mint/35 p-3">
          <strong>
            {check.level > check.previous_level
              ? `ارتفع مستواك من ${check.previous_level} إلى ${check.level}`
              : check.level < check.previous_level
                ? `مستواك صار ${check.level} من 4`
                : `مستواك ${check.level} من 4`}
            {check.expected_level !== null && `، والمطلوب ${check.expected_level}`}
          </strong>
          <span className="text-sm text-muted">{check.reason}</span>
          <Button className="self-start" onClick={onLevelChanged}>
            حدّثي مساري
          </Button>
        </div>
      ) : (
        <>
          <form onSubmit={submit} className="flex flex-col gap-2">
            <label className="flex flex-col gap-2 text-sm text-muted">
              جوابك
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                rows={2}
                maxLength={2000}
                className="rounded-xl border border-line bg-surface p-3 font-body text-ink"
              />
            </label>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={!draft.trim() || waiting}>
                أرسلي
              </Button>
              {answers >= MIN_ANSWERS && (
                <Button variant="ai" onClick={checkLevel} disabled={waiting || checking}>
                  {checking ? 'تمّام يقيّم إجاباتك…' : 'قيّمي مستواي'}
                </Button>
              )}
            </div>
          </form>
          {answers < MIN_ANSWERS && (
            <p className="m-0 text-xs text-faint">
              جاوبي {MIN_ANSWERS - answers} {MIN_ANSWERS - answers === 1 ? 'سؤال' : 'أسئلة'} عشان يقدر تمّام يقيّم مستواك.
            </p>
          )}
        </>
      )}
    </div>
  )
}
