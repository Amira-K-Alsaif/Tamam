import { Check, RotateCcw } from 'lucide-react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { ProgressBar } from '../../components/ProgressBar'
import type { ProcedureStep } from './proceduresApi'
import { useChecklist } from './useChecklist'

type StepState = 'done' | 'current' | 'upcoming'

const STATE_LABEL: Record<StepState, string> = {
  done: 'مكتملة',
  current: 'الحالية',
  upcoming: 'القادمة',
}

// The three step markers from the brand guide: filled, outlined with a glow, faint outline.
const MARKER: Record<StepState, string> = {
  done: 'bg-mint',
  current: 'border-2 border-mint bg-night shadow-lg shadow-mint/40',
  upcoming: 'border-2 border-faint/60 bg-night',
}

/** The procedure as a stepper: finish the current step, and the next one becomes current. */
export function ProcedureSteps({ procedureId, steps }: { procedureId: string; steps: ProcedureStep[] }) {
  const ordered = [...steps].sort((a, b) => a.order - b.order)
  const checklist = useChecklist(`${procedureId}.steps`)
  const key = (step: ProcedureStep) => String(step.order)
  const doneCount = ordered.filter((step) => checklist.isChecked(key(step))).length
  const current = ordered.find((step) => !checklist.isChecked(key(step)))
  const finished = current === undefined

  function stateOf(step: ProcedureStep): StepState {
    if (checklist.isChecked(key(step))) return 'done'
    return step === current ? 'current' : 'upcoming'
  }

  return (
    <Card
      title="الخطوات"
      action={
        doneCount > 0 && (
          <Button variant="secondary" className="h-9 px-4" onClick={checklist.reset}>
            <RotateCcw aria-hidden className="size-4" strokeWidth={1.8} />
            ابدئي من جديد
          </Button>
        )
      }
    >
      <ProgressBar label={`أنجزتِ ${doneCount} من ${ordered.length} خطوات`} value={(doneCount / ordered.length) * 100} />

      {finished && (
        <div role="status" className="flex items-center gap-3 rounded-2xl bg-aurora p-4 font-semibold text-night">
          <Check aria-hidden className="size-5" strokeWidth={2.4} />
          تمّ! خلّصتي كل خطوات الإجراء.
        </div>
      )}

      <ol aria-label="خطوات الإجراء" className="m-0 flex list-none flex-col p-0">
        {ordered.map((step, index) => {
          const state = stateOf(step)
          const last = index === ordered.length - 1
          return (
            <li key={step.order} aria-current={state === 'current' ? 'step' : undefined} className="flex gap-4">
              <div className="flex flex-col items-center pt-2">
                <span aria-hidden="true" className={`size-4 shrink-0 rotate-45 rounded-sm ${MARKER[state]}`} />
                {!last && <span aria-hidden="true" className="my-2 w-px flex-1 bg-line-strong" />}
              </div>

              <div
                className={`mb-3 flex flex-1 flex-col gap-2 rounded-2xl p-4 ${
                  state === 'current' ? 'border border-mint/35 bg-raised' : ''
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3
                    className={`m-0 text-base font-semibold ${state === 'upcoming' ? 'text-muted' : 'text-ink'}`}
                  >
                    <span className="font-display text-mint">{step.order}.</span> {step.title}
                  </h3>
                  <span className={`text-xs ${state === 'current' ? 'text-mint' : 'text-faint'}`}>
                    {STATE_LABEL[state]}
                  </span>
                </div>
                <p className={`m-0 text-sm ${state === 'done' ? 'text-faint' : 'text-soft'}`}>{step.detail}</p>

                {state === 'current' && (
                  <div className="pt-1">
                    <Button className="h-9 px-4" onClick={() => checklist.check(key(step))}>
                      {last ? 'تمّت، آخر خطوة' : 'تمّت، التالي'}
                    </Button>
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}
