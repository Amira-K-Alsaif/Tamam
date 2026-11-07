import { ArrowLeft } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Card } from '../../components/Card'
import { PageHeader } from '../../components/PageHeader'
import { askQuestion, type AskResponse } from '../../lib/api'

type Message = { role: 'user'; text: string } | { role: 'assistant'; reply: AskResponse }

const SUGGESTIONS = ['كم يوم إجازتي في السنة؟', 'أبي أشتغل من البيت', 'كيف أطلب صلاحية نظام؟']

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const lastReply = messages.findLast((message) => message.role === 'assistant')
  const sources = lastReply?.role === 'assistant' ? lastReply.reply.sources : []

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = question.trim()
    if (!text || loading) return

    setMessages((current) => [...current, { role: 'user', text }])
    setQuestion('')
    setError(null)
    setLoading(true)
    try {
      const reply = await askQuestion(text)
      setMessages((current) => [...current, { role: 'assistant', reply }])
    } catch {
      setError('تعذّر الوصول للخادم. تأكد إنه شغال وحاول مرة ثانية.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader title="اسأل عن إجراء" description="إجابات من وثائق الشركة، ومعها المصدر دائماً." />

      <div className="flex flex-wrap items-start gap-6">
        <section aria-label="المحادثة" className="main-column flex min-w-0 flex-col gap-5">
          {messages.length === 0 && (
            <Card title="جرّب تسأل">
              <div className="flex flex-wrap gap-2.5">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setQuestion(suggestion)}
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
              <p
                key={index}
                className="m-0 max-w-xl self-end rounded-3xl rounded-es-md bg-raised px-5 py-3"
              >
                {message.text}
              </p>
            ) : (
              <div key={index} className="flex items-start gap-3">
                <span aria-hidden="true" className="size-9 shrink-0 rounded-full bg-aurora" />
                <p
                  className={`m-0 max-w-2xl whitespace-pre-line rounded-2xl px-5 py-3 ${
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

          <form
            onSubmit={handleSubmit}
            className="flex h-15 items-center gap-3 rounded-full border border-mint/35 bg-surface ps-5 pe-2 focus-within:border-mint"
          >
            <label htmlFor="chat-question" className="sr-only">
              سؤالك
            </label>
            <input
              id="chat-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="اكتب سؤالك…"
              className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none"
            />
            <button
              type="submit"
              aria-label="إرسال"
              disabled={loading}
              className="flex size-11 shrink-0 items-center justify-center rounded-full bg-aurora text-night disabled:opacity-50"
            >
              <ArrowLeft aria-hidden className="size-5" />
            </button>
          </form>
        </section>

        <aside aria-label="مصادر الإجابة" className="side-column flex flex-col gap-3">
          <h2 className="m-0 font-display text-lg font-semibold">مصادر الإجابة</h2>
          {sources.length === 0 ? (
            <p className="m-0 text-sm text-faint">بتظهر هنا مصادر آخر إجابة.</p>
          ) : (
            sources.map((source, index) => (
              <article
                key={`${source.document_id}-${source.page}`}
                className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4"
              >
                <strong className="text-sm">
                  [{index + 1}] {source.document_title}
                </strong>
                <span className="text-xs text-faint">
                  صفحة {source.page} · {source.section_title}
                </span>
                <p className="m-0 text-sm leading-relaxed text-soft">{source.quote}</p>
              </article>
            ))
          )}
        </aside>
      </div>
    </>
  )
}
