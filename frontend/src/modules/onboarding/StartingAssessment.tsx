import { useEffect, useState } from 'react'

import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { ProgressBar } from '../../components/ProgressBar'
import { answerAssessment, getAssessment, uploadCv } from '../../lib/api'
import type { Assessment, AssessmentOutcome, CvSkill } from '../../lib/api'

const CV_TYPES = '.pdf,.docx,.txt'
const SECTION_TITLES = { company: 'عن الشركة', skill: 'عن تخصصك' } as const

// Every employee starts here. Their CV (optional) says which skills they have; the questions
// measure what they know about the company and how well they know their specialization. The
// path is drawn from the result, so nothing else shows until it is done.
export function StartingAssessment({ employeeId, onDone }: { employeeId: string; onDone: () => void }) {
  const [step, setStep] = useState<'cv' | 'questions'>('cv')

  return (
    <Card title="قبل ما نبدأ: تقييمك الأولي">
      <p className="m-0 text-muted">
        نبي نعرف وش تعرفين عن الشركة ووين مستواك في تخصصك، عشان يرسم لك تمّام مسار بدايتك: وش تحتاجين تتعلمين،
        ووش تطوّرين من مهاراتك.
      </p>
      {step === 'cv' ? (
        <CvStep employeeId={employeeId} onNext={() => setStep('questions')} />
      ) : (
        <QuestionsStep employeeId={employeeId} onDone={onDone} />
      )}
    </Card>
  )
}

function CvStep({ employeeId, onNext }: { employeeId: string; onNext: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [state, setState] = useState<'idle' | 'reading' | 'unreadable' | 'unavailable'>('idle')
  const [skills, setSkills] = useState<CvSkill[] | null>(null)

  async function read() {
    if (!file) return
    setState('reading')
    try {
      setSkills(await uploadCv(file, employeeId))
      setState('idle')
    } catch (error) {
      const status = (error as { status?: number }).status
      setState(status === 422 ? 'unreadable' : 'unavailable')
    }
  }

  if (skills) {
    return (
      <div className="flex flex-col gap-3 rounded-2xl border border-line bg-sunken p-4">
        <strong>{skills.length > 0 ? 'هذي المهارات اللي لقيناها في سيرتك' : 'ما لقينا مهارات واضحة في سيرتك'}</strong>
        {skills.length > 0 && (
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {skills.map((skill) => (
              <li key={skill.skill_id} className="flex flex-col">
                <span>{skill.label_ar}</span>
                <span className="text-xs text-faint">من سيرتك: «{skill.quote}»</span>
              </li>
            ))}
          </ul>
        )}
        <p className="m-0 text-sm text-muted">بنتأكد من مستواك فيها بأسئلة قصيرة.</p>
        <Button variant="ai" className="self-start" onClick={onNext}>
          ابدئي الأسئلة
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-line bg-sunken p-4">
      <strong>١. أرفقي سيرتك الذاتية (اختياري)</strong>
      <p className="m-0 text-sm text-muted">نقرأ منها مهاراتك بس، وما نحتفظ بالملف. PDF أو Word أو نص.</p>
      <label className="flex flex-col gap-2 text-sm">
        السيرة الذاتية
        <input
          type="file"
          accept={CV_TYPES}
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null)
            setState('idle')
          }}
          className="text-muted"
        />
      </label>
      {state === 'reading' && (
        <p role="status" className="m-0 text-sm text-muted">
          تمّام يقرأ سيرتك…
        </p>
      )}
      {state === 'unreadable' && (
        <p role="alert" className="m-0 text-sm text-warning">
          ما قدرنا نقرأ الملف. جرّبي PDF أو Word أو ملف نص أصغر من ٢ ميجا.
        </p>
      )}
      {state === 'unavailable' && (
        <p role="alert" className="m-0 text-sm text-warning">
          قراءة السيرة ما تشتغل الحين. تقدرين تكمّلين بدونها.
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button variant="ai" onClick={read} disabled={!file || state === 'reading'}>
          اقرأ سيرتي
        </Button>
        <Button variant="secondary" onClick={onNext} disabled={state === 'reading'}>
          كمّلي بدون سيرة
        </Button>
      </div>
    </div>
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
        تمّام يجهّز أسئلتك من وثائق الشركة ومهارات تخصصك…
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
      <strong>٢. الأسئلة</strong>
      {questions.map((question, index) => {
        const previous = questions[index - 1]
        const newSection = index === 0 || previous.kind !== question.kind
        const newTopic = newSection || previous.topic !== question.topic
        return (
          <fieldset key={`${question.topic}-${question.question}`} className="m-0 flex flex-col gap-2 border-0 p-0">
            {newSection && <h3 className="m-0 font-display text-lg">{SECTION_TITLES[question.kind]}</h3>}
            {newTopic && <p className="m-0 text-sm font-semibold text-mint">{question.topic}</p>}
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
            {outcome && question.source && (
              <p className="m-0 text-xs text-faint">
                المصدر: {question.source.document_title} · {question.source.section_title} · «{question.source.quote}»
              </p>
            )}
          </fieldset>
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
      <strong>٣. نتيجتك</strong>
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
