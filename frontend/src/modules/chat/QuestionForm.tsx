import { ArrowLeft } from 'lucide-react'
import type { FormEvent } from 'react'

type QuestionFormProps = {
  value: string
  disabled: boolean
  onChange: (value: string) => void
  onSubmit: () => void
}

/** The question box. Its outer border shows keyboard focus instead of the input's. */
export function QuestionForm({ value, disabled, onChange, onSubmit }: QuestionFormProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex h-15 items-center gap-3 rounded-full border border-mint/35 bg-surface ps-5 pe-2 focus-within:border-mint"
    >
      <label htmlFor="chat-question" className="sr-only">
        سؤالك
      </label>
      <input
        id="chat-question"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="اكتب سؤالك…"
        className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none"
      />
      <button
        type="submit"
        aria-label="إرسال"
        disabled={disabled}
        className="flex size-11 shrink-0 items-center justify-center rounded-full bg-aurora text-night disabled:opacity-50"
      >
        {/* Points left: "forward" in a right-to-left layout. */}
        <ArrowLeft aria-hidden className="size-5" />
      </button>
    </form>
  )
}
