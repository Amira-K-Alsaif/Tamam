import { Copy, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { PageHeader } from '../../components/PageHeader'
import { ProgressBar } from '../../components/ProgressBar'
import { arabicCount, FIELDS } from './arabicCount'
import { BackLink } from './ProcedureDetail'
import type { CompanyForm, FormField } from './proceduresApi'
import { SourceCard } from './SourceCard'
import { useFormFill } from './useFormFill'
import { useCompanyForm } from './useProcedures'

/** One company form: «عبّي النموذج عني» fills what the profile knows, the employee types the rest. */
export function FormFiller({ id }: { id: string }) {
  const state = useCompanyForm(id)

  return (
    <>
      <BackLink />
      {state.kind === 'loading' && (
        <p role="status" className="m-0 text-muted">
          جاري تحميل النموذج…
        </p>
      )}
      {state.kind === 'not-found' && (
        <Card>
          <p role="alert" className="m-0 text-warning">
            ما لقينا هذا النموذج. ارجعي لكل الإجراءات واختاري واحد منها.
          </p>
        </Card>
      )}
      {state.kind === 'error' && (
        <Card>
          <p role="alert" className="m-0 text-danger">
            ما قدرنا نجيب النموذج. تأكدي إن الخادم شغّال وحاولي مرة ثانية.
          </p>
        </Card>
      )}
      {state.kind === 'ready' && <FormView form={state.form} />}
    </>
  )
}

type CopyStatus = 'idle' | 'copied' | 'incomplete' | 'failed'

function FormView({ form }: { form: CompanyForm }) {
  const fill = useFormFill(form)
  const [copy, setCopy] = useState<CopyStatus>('idle')
  const answered = form.fields.length - fill.missing.length

  async function copyForm() {
    if (fill.missing.length > 0) {
      setCopy('incomplete')
      return
    }
    try {
      await navigator.clipboard.writeText(fill.asText())
      setCopy('copied')
    } catch {
      setCopy('failed')
    }
  }

  return (
    <>
      <PageHeader title={form.title} description={`${form.department} · ${arabicCount(form.fields.length, FIELDS)}`} />

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <div className="flex min-w-0 flex-col gap-6 lg:col-span-2">
          {fill.canPrefill && <AssistPanel fill={fill} />}

          <Card title="الحقول">
            <ProgressBar
              label={`عبّيتِ ${answered} من ${form.fields.length}`}
              value={(answered / form.fields.length) * 100}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              {form.fields.map((field, index) => (
                <Field
                  key={field.label}
                  id={`${form.id}-field-${index}`}
                  field={field}
                  value={fill.values[field.label] ?? ''}
                  fromProfile={fill.isFromProfile(field.label)}
                  onChange={(value) => {
                    fill.setValue(field.label, value)
                    setCopy('idle')
                  }}
                />
              ))}
            </div>

            <div className="flex flex-col gap-3 border-t border-line pt-4">
              <Button className="self-start" onClick={copyForm}>
                <Copy aria-hidden className="size-4" strokeWidth={1.8} />
                انسخي النموذج
              </Button>
              {copy === 'copied' && (
                <p role="status" className="m-0 text-sm text-mint">
                  نسخنا النموذج. الصقيه في المكان اللي تقوله «طريقة التقديم».
                </p>
              )}
              {copy === 'incomplete' && (
                <p role="alert" className="m-0 text-sm text-warning">
                  باقي تعبّين: {fill.missing.join('، ')}.
                </p>
              )}
              {copy === 'failed' && (
                <p role="alert" className="m-0 text-sm text-danger">
                  ما قدرنا ننسخ. حددي الحقول وانسخيها بنفسك.
                </p>
              )}
            </div>
          </Card>
        </div>

        <div className="flex min-w-0 flex-col gap-6">
          {form.instructions && (
            <Card title="طريقة التقديم">
              <p className="m-0 text-soft">{form.instructions}</p>
            </Card>
          )}
          <SourceCard source={form.source} label="مصدر النموذج" />
        </div>
      </div>
    </>
  )
}

function AssistPanel({ fill }: { fill: ReturnType<typeof useFormFill> }) {
  const { status } = fill
  return (
    <section
      aria-label="تعبئة تلقائية"
      className="flex flex-col gap-4 rounded-3xl border border-line bg-surface bg-aurora-glow p-6"
    >
      <div className="flex items-center gap-4">
        <span aria-hidden="true" className="size-10 shrink-0 rounded-full bg-aurora shadow-2xl shadow-mint/40" />
        <div className="flex flex-col">
          <h2 className="m-0 font-display text-lg font-semibold">خلّي تمّام يعبّي اللي يعرفه</h2>
          <span className="text-sm text-muted">نعبّي من ملفك الوظيفي، وتراجعين كل شي قبل ما تنسخين.</span>
        </div>
      </div>
      <Button variant="ai" className="self-start" disabled={status.kind === 'filling'} onClick={fill.fillFromProfile}>
        <Sparkles aria-hidden className="size-4" strokeWidth={1.8} />
        {status.kind === 'filling' ? 'جاري التعبئة…' : 'عبّي النموذج عني'}
      </Button>
      {status.kind === 'filled' && (
        <p role="status" className="m-0 text-sm text-soft">
          تعبّى {arabicCount(status.count, FIELDS)} من ملفك. كمّلي الباقي.
        </p>
      )}
      {status.kind === 'error' && (
        <p role="alert" className="m-0 text-sm text-danger">
          ما قدرنا نوصل لملفك. تأكدي إن الخادم شغّال، أو عبّي الحقول بنفسك.
        </p>
      )}
    </section>
  )
}

const INPUT =
  'w-full rounded-xl border bg-sunken px-4 text-base text-ink outline-none scheme-dark placeholder:text-faint focus:border-mint'

type FieldProps = {
  id: string
  field: FormField
  value: string
  fromProfile: boolean
  onChange: (value: string) => void
}

function Field({ id, field, value, fromProfile, onChange }: FieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${field.kind === 'long_text' ? 'sm:col-span-2' : ''}`}>
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={id} className="text-sm text-muted">
          {field.label}
        </label>
        {fromProfile && <span className="text-xs text-mint">من ملفك</span>}
      </div>
      {field.kind === 'long_text' ? (
        <textarea
          id={id}
          rows={4}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={`${INPUT} border-line py-3`}
        />
      ) : (
        <input
          id={id}
          type={field.kind === 'date' ? 'date' : field.kind === 'number' ? 'number' : 'text'}
          min={field.kind === 'number' ? 1 : undefined}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={`${INPUT} h-11 ${fromProfile ? 'border-mint/40' : 'border-line'}`}
        />
      )}
    </div>
  )
}
