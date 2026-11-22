import { useEffect, useState } from 'react'

import { Button } from '../../components/Button'
import { answerLessonQuiz, getLessonQuiz } from '../../lib/api'
import type { Quiz, QuizResult } from '../../lib/api'

type QuizState =
  | { kind: 'loading' }
  | { kind: 'unavailable' }
  | { kind: 'ready'; quiz: Quiz }

// A short quiz on one lesson, generated from its policy document. Passing it takes the lesson
// off the roadmap; `onAnswered` lets the page reload the roadmap, progress, and badges.
export function LessonQuiz({
  documentId,
  employeeId,
  onAnswered,
}: {
  documentId: string
  employeeId: string
  onAnswered: () => void
}) {
  const [state, setState] = useState<QuizState>({ kind: 'loading' })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    let cancelled = false
    getLessonQuiz(documentId)
      .then((quiz) => {
        if (!cancelled) setState({ kind: 'ready', quiz })
      })
      .catch(() => {
        if (!cancelled) setState({ kind: 'unavailable' })
      })
    return () => {
      cancelled = true
    }
  }, [documentId])

  if (state.kind === 'loading') {
    return <p className="m-0 text-sm text-muted">جاري تجهيز الاختبار من الوثيقة…</p>
  }
  if (state.kind === 'unavailable') {
    return (
      <p className="m-0 text-sm text-warning">
        الاختبار ما تجهّز. حاولي مرة ثانية بعد شوي.
      </p>
    )
  }

  const { quiz } = state
  const complete = quiz.questions.every((_, index) => answers[index] !== undefined)

  async function submit() {
    setSending(true)
    try {
      const answered = await answerLessonQuiz(
        documentId,
        quiz.questions.map((_, index) => answers[index]),
        employeeId,
      )
      setResult(answered)
      onAnswered()
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-line bg-sunken p-4">
      <p className="m-0 text-sm text-faint">اختبار قصير من «{quiz.document_title}»</p>
      {quiz.questions.map((question, index) => (
        <fieldset key={question.question} className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="mb-2 font-semibold">
            {index + 1}. {question.question}
          </legend>
          {question.options.map((option, optionIndex) => {
            const isRight = result?.correct_options[index] === optionIndex
            const isWrongPick = result && answers[index] === optionIndex && !isRight
            return (
              <label
                key={option}
                className={`flex cursor-pointer items-center gap-2 rounded-xl px-3 py-1.5 ${
                  isRight ? 'bg-mint/12 text-mint' : isWrongPick ? 'bg-danger/16 text-danger' : ''
                }`}
              >
                <input
                  type="radio"
                  name={`q-${index}`}
                  checked={answers[index] === optionIndex}
                  disabled={result !== null}
                  onChange={() => setAnswers({ ...answers, [index]: optionIndex })}
                />
                {option}
                {isRight && result && <span className="text-xs">الجواب الصحيح</span>}
              </label>
            )
          })}
          {result && (
            <p className="m-0 text-xs text-faint">
              المصدر: {question.source.section_title} · «{question.source.quote}»
            </p>
          )}
        </fieldset>
      ))}
      {result ? (
        <p className={`m-0 font-semibold ${result.passed ? 'text-mint' : 'text-warning'}`}>
          {result.passed
            ? `درجتك ${result.score}٪. نجحتي، والدرس طلع من مسارك.`
            : `درجتك ${result.score}٪. المطلوب ٧٠٪، راجعي الوثيقة وأعيدي الاختبار.`}
        </p>
      ) : (
        <Button onClick={submit} disabled={!complete || sending}>
          {sending ? 'جاري التصحيح…' : 'سلّمي الإجابات'}
        </Button>
      )}
    </div>
  )
}
