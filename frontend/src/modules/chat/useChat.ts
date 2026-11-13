import { useState } from 'react'
import { askQuestion, type AskResponse, type Source } from '../../lib/api'

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
    } catch {
      setError('تعذّر الوصول للخادم. تأكد إنه شغال وحاول مرة ثانية.')
    } finally {
      setLoading(false)
    }
  }

  return { messages, sources, loading, error, ask }
}
