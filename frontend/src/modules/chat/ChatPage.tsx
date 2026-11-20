import { useState } from 'react'
import { PageHeader } from '../../components/PageHeader'
import { MessageList } from './MessageList'
import { QuestionForm } from './QuestionForm'
import { SourcesPanel } from './SourcesPanel'
import { useChat } from './useChat'

/** «اسأل عن إجراء»: answers from the company documents, with the sources beside them. */
export default function ChatPage() {
  const { messages, sources, loading, error, ask } = useChat()
  const [question, setQuestion] = useState('')

  function send() {
    void ask(question)
    setQuestion('')
  }

  return (
    <>
      <PageHeader title="اسأل عن إجراء" description="إجابات من وثائق الشركة، ومعها المصدر دائماً." />

      <div className="flex flex-wrap items-start gap-6">
        <section aria-label="المحادثة" className="main-column flex min-w-0 flex-col gap-5">
          <MessageList messages={messages} loading={loading} error={error} onSuggestion={setQuestion} />
          <QuestionForm value={question} disabled={loading} onChange={setQuestion} onSubmit={send} />
        </section>

        <SourcesPanel sources={sources} />
      </div>
    </>
  )
}
