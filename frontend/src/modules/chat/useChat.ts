import { useState } from 'react'
import { ApiError, askQuestion, type AskResponse, type Source } from '../../lib/api'

export type Message = { role: 'user'; text: string } | { role: 'assistant'; reply: AskResponse }

/** The conversation state and the action that sends a question to the backend. */
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const lastReply = messages.findLast((message) => message.role === 'assistant')
  const sources: Source[] = lastReply?.role === 'assistant' ? lastReply.reply.sources : []

  async function ask(question: string) {
    const text = question.trim()
    if (!text || loading) return

    setMessages((current) => [...current, { role: 'user', text }])
    setError(null)
    setLoading(true)
    try {
      const reply = await askQuestion(text)
      setMessages((current) => [...current, { role: 'assistant', reply }])
    } catch (caught) {
      setError(
        // 503: the server is up but the answering service is busy or not set up.
        caught instanceof ApiError && caught.status === 503
          ? 'خدمة الإجابة غير متاحة حالياً. حاول بعد قليل.'
          : 'تعذّر الوصول للخادم. تأكد إنه شغال وحاول مرة ثانية.',
      )
    } finally {
      setLoading(false)
    }
  }

  return { messages, sources, loading, error, ask }
}
