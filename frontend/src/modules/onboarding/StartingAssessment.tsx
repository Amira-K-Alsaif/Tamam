import { useEffect, useState } from 'react'

import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { ProgressBar } from '../../components/ProgressBar'
import { answerAssessment, getAssessment } from '../../lib/api'
import type { Assessment, AssessmentOutcome } from '../../lib/api'

type AssessmentState = { kind: 'loading' } | { kind: 'unavailable' } | { kind: 'ready'; assessment: Assessment }

// A new hire's first step: questions generated from the company policies. The scores decide
// which topics become lessons on the roadmap, instead of a guess.
export function StartingAssessment({ employeeId, onDone }: { employeeId: string; onDone: () => void }) {
  const [started, setStarted] = useState(false)

  return (
    <Card title="ابدئي بالتقييم الأولي">
      <p className="m-0 text-muted">
        أسئلة قصيرة من سياسات الشركة يجهّزها تمّام لك. على حسب إجاباتك نعرف وش تعرفين، ونرتّب دروسك.
      </p>
      {started ? (
        <AssessmentQuestions employeeId={employeeId} onDone={onDone} />
      ) : (
        <Button variant="ai" className="self-start" onClick={() => setStarted(true)}>
          ابدئي التقييم
        </Button>
      )}
    </Card>
  )
}

function AssessmentQuestions({ employeeId, onDone }: { employeeId: string; onDone: () => void }) {
  const [state, setState] = useState<AssessmentState>({ kind: 'loading' })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [outcome, setOutcome] = useState<AssessmentOutcome | null>(null)
  const [sending, setSending] = useState(false)
  const [sendFailed, setSendFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    getAssessment()
      .then((assessment) => {
        if (!cancelled) setState({ kind: 'ready', assessment })
      })
      .catch(() => {
        if (!cancelled) setState({ kind: 'unavailable' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (state.kind === 'loading') {
    return (
      <p role="status" className="m-0 text-sm text-muted">
        تمّام يجهّز أسئلتك من وثائق الشركة…
      </p>
    )
  }
  if (state.kind === 'unavailable') {
    return (
      <p role="alert" className="m-0 text-sm text-warning">
        التقييم ما تجهّز. حاولي مرة ثانية بعد شوي.
      </p>
    )
  }

  const { questions } = state.assessment
  const complete = questions.every((_, index) => answers[index] !== undefined)

  async function submit() {
    setSending(true)
    setSendFailed(false)
    try {
      setOutcome(await answerAssessment(questions.map((_, index) => answers[index]), employeeId))
    } catch {
      setSendFailed(true)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-line bg-sunken p-4">
      {questions.map((question, index) => {
        const firstOfTopic = index === 0 || questions[index - 1].topic !== question.topic
        return (
          <fieldset key={`${question.topic}-${question.question}`} className="m-0 flex flex-col gap-2 border-0 p-0">
            {firstOfTopic && <p className="m-0 text-sm font-semibold text-mint">{question.topic}</p>}
            <legend className="mb-2 font-semibold">
              {index + 1}. {question.question}
            </legend>
            {question.options.map((option, optionIndex) => {
              const isRight = outcome?.correct_options[index] === optionIndex
              const isWrongPick = outcome && answers[index] === optionIndex && !isRight
              return (
                <label
                  key={option}
                  className={`flex cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 ${
                    isRight ? 'bg-mint/12 text-mint' : isWrongPick ? 'bg-danger/16 text-danger' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name={`assessment-${index}`}
                    checked={answers[index] === optionIndex}
                    disabled={outcome !== null}
                    onChange={() => setAnswers({ ...answers, [index]: optionIndex })}
                  />
                  {option}
                  {isRight && outcome && <span className="text-xs">الجواب الصحيح</span>}
                </label>
              )
            })}
            {outcome && (
              <p className="m-0 text-xs text-faint">
                المصدر: {question.source.document_title} · {question.source.section_title} · «{question.source.quote}»
              </p>
            )}
          </fieldset>
        )
      })}

      {outcome ? (
        <div className="flex flex-col gap-3">
          <strong>نتيجتك في كل موضوع</strong>
          {outcome.scores.map((topic) => (
            <ProgressBar
              key={topic.topic}
              label={`${topic.topic}: ${topic.passed ? 'تعرفينه' : 'صار درس في مسارك'}`}
              value={topic.score}
            />
          ))}
          <Button className="self-start" onClick={onDone}>
            اعرضي مساري
          </Button>
        </div>
      ) : (
        <>
          {sendFailed && (
            <p role="alert" className="m-0 text-sm text-danger">
              ما قدرنا نصحّح إجاباتك. حاولي مرة ثانية.
            </p>
          )}
          <Button onClick={submit} disabled={!complete || sending}>
            {sending ? 'جاري التصحيح…' : 'سلّمي الإجابات'}
          </Button>
        </>
      )}
    </div>
  )
}
