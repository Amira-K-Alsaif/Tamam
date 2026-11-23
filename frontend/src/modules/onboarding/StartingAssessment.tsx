import { Fragment, useEffect, useState } from 'react'

import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { ProgressBar } from '../../components/ProgressBar'
import { answerAssessment, getAssessment } from '../../lib/api'
import type { Assessment, AssessmentOutcome } from '../../lib/api'

const SECTION_TITLES = { company: 'عن الشركة', skill: 'عن تخصصك: وين مستواك؟' } as const

// Every employee starts here: questions on the company's policies, and their own level in each
// skill of their specialization. The path is drawn from the answers, so nothing else shows
// until it is done.
export function StartingAssessment({ employeeId, onDone }: { employeeId: string; onDone: () => void }) {
  return (
    <Card title="قبل ما نبدأ: تقييمك الأولي">
      <p className="m-0 text-muted">
        نبي نعرف وش تعرفين عن الشركة ووين مستواك في تخصصك، عشان يرسم لك تمّام مسار بدايتك: وش تحتاجين تتعلمين،
        ووش تطوّرين من مهاراتك.
      </p>
      <QuestionsStep employeeId={employeeId} onDone={onDone} />
    </Card>
  )
}

type QuestionsState = { kind: 'loading' } | { kind: 'unavailable' } | { kind: 'ready'; assessment: Assessment }

function QuestionsStep({ employeeId, onDone }: { employeeId: string; onDone: () => void }) {
  const [state, setState] = useState<QuestionsState>({ kind: 'loading' })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [outcome, setOutcome] = useState<AssessmentOutcome | null>(null)
  const [sending, setSending] = useState(false)
  const [sendFailed, setSendFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    getAssessment(employeeId)
      .then((assessment) => {
        if (!cancelled) setState({ kind: 'ready', assessment })
      })
      .catch(() => {
        if (!cancelled) setState({ kind: 'unavailable' })
      })
    return () => {
      cancelled = true
    }
  }, [employeeId])

  if (state.kind === 'loading') {
    return (
      <p role="status" className="m-0 text-sm text-muted">
        نجهّز أسئلتك…
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
        const previous = questions[index - 1]
        const newSection = index === 0 || previous.kind !== question.kind
        const newTopic = newSection || previous.topic !== question.topic
        return (
          // Headings sit outside the fieldset: a browser always draws a legend first in its fieldset.
          <Fragment key={`${question.topic}-${question.question}`}>
            {newSection && <h3 className="m-0 mt-2 font-display text-lg">{SECTION_TITLES[question.kind]}</h3>}
            {newTopic && question.kind === 'company' && (
              <p className="m-0 text-sm font-semibold text-mint">{question.topic}</p>
            )}
            <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
              <legend className="mb-2 font-semibold">
                {index + 1}. {question.question}
              </legend>
              {question.options.map((option, optionIndex) => {
                // Self-rated skill questions have no right answer, so only company ones are marked.
                const isRight = outcome !== null && outcome.correct_options[index] === optionIndex
                const isWrongPick =
                  outcome !== null && question.kind === 'company' && answers[index] === optionIndex && !isRight
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
              {outcome && question.source && (
                <p className="m-0 text-xs text-faint">
                  المصدر: {question.source.document_title} · {question.source.section_title} · «{question.source.quote}»
                </p>
              )}
            </fieldset>
          </Fragment>
        )
      })}

      {outcome ? (
        <Outcome outcome={outcome} onDone={onDone} />
      ) : (
        <>
          {sendFailed && (
            <p role="alert" className="m-0 text-sm text-danger">
              ما قدرنا نصحّح إجاباتك. حاولي مرة ثانية.
            </p>
          )}
          <Button onClick={submit} disabled={!complete || sending}>
            {sending ? 'تمّام يصحّح ويرسم مسارك…' : 'سلّمي الإجابات'}
          </Button>
        </>
      )}
    </div>
  )
}

function Outcome({ outcome, onDone }: { outcome: AssessmentOutcome; onDone: () => void }) {
  return (
    <div className="flex flex-col gap-3">
      <strong>نتيجتك</strong>
      {outcome.topics.map((topic) => (
        <ProgressBar
          key={topic.document_id}
          label={`${topic.topic}: ${topic.passed ? 'تعرفينها' : 'صارت درس في مسارك'}`}
          value={topic.score}
        />
      ))}
      {outcome.skills.map((skill) => (
        <ProgressBar
          key={skill.skill_id}
          label={`${skill.label_ar}: مستواك ${skill.level} من 4${
            skill.expected_level === null ? '' : `، ومسماك يحتاج ${skill.expected_level}`
          }`}
          value={skill.level * 25}
        />
      ))}
      <Button variant="ai" className="self-start" onClick={onDone}>
        اعرضي مساري
      </Button>
    </div>
  )
}
