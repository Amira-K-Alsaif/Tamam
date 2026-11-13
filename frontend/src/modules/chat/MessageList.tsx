import { Card } from '../../components/Card'
import type { Message } from './useChat'

const SUGGESTIONS = ['كم يوم إجازتي في السنة؟', 'أبي أشتغل من البيت', 'كيف أطلب صلاحية نظام؟']

type MessageListProps = {
  messages: Message[]
  loading: boolean
  error: string | null
  onSuggestion: (question: string) => void
}

/** The conversation, with its empty, loading, and error states. */
export function MessageList({ messages, loading, error, onSuggestion }: MessageListProps) {
  return (
    <>
      {messages.length === 0 && (
        <Card title="جرّب تسأل">
          <div className="flex flex-wrap gap-2.5">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => onSuggestion(suggestion)}
                className="h-10 rounded-full border border-line bg-white/5 px-4 text-sm text-soft"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </Card>
      )}

      {messages.map((message, index) =>
        message.role === 'user' ? (
          <p key={index} className="m-0 max-w-xl self-end rounded-3xl rounded-es-md bg-raised px-5 py-3">
            {message.text}
          </p>
        ) : (
          <div key={index} className="flex items-start gap-3">
            <span aria-hidden="true" className="size-9 shrink-0 rounded-full bg-aurora" />
            <p
              className={`m-0 max-w-2xl whitespace-pre-line rounded-2xl px-5 py-3 ${
                // "Not found" gets a dashed outline so it never reads like a real answer.
                message.reply.found ? '' : 'border border-dashed border-line-strong text-muted'
              }`}
            >
              {message.reply.answer}
            </p>
          </div>
        ),
      )}

      {loading && (
        <p role="status" className="m-0 text-sm text-faint">
          تمّام يبحث في الوثائق…
        </p>
      )}

      {error && (
        <p role="alert" className="m-0 text-sm text-danger">
          {error}
        </p>
      )}
    </>
  )
}
