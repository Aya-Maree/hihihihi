import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Bot, User, BookOpen, AlertTriangle, Loader2, Globe } from 'lucide-react'
import clsx from 'clsx'

export default function ChatBox({ messages, onSend, loading, workflowState }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = (e) => {
    e.preventDefault()
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    onSend(msg)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const quickReplies = getQuickReplies(workflowState)

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto chat-scroll space-y-4 p-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Your AI Event Planner</h3>
            <p className="text-sm text-gray-500 max-w-xs">
              Tell me about the event you're planning — I'll guide you through the process
              and generate a complete plan with checklist, shopping list, and schedule.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-purple-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />
              <span className="text-sm text-gray-500">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick replies */}
      {quickReplies.length > 0 && !loading && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {quickReplies.map((reply, i) => (
            <button
              key={i}
              onClick={() => {
                setInput(reply)
                inputRef.current?.focus()
              }}
              className="text-xs px-3 py-1.5 bg-purple-50 text-purple-700 rounded-full border border-purple-200 hover:bg-purple-100 transition-colors"
            >
              {reply}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your event or ask a question..."
            rows={2}
            disabled={loading}
            className="flex-1 resize-none input min-h-[44px] max-h-[120px]"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="btn-primary p-2.5 flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-1">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  )
}

function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const hasCitations = message.citations && message.citations.length > 0
  const hasConflicts = message.conflicts && message.conflicts.length > 0

  return (
    <div className={clsx('flex items-start gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-purple-600' : 'bg-purple-100'
        )}
      >
        {isUser
          ? <User className="w-4 h-4 text-white" />
          : <Bot className="w-4 h-4 text-purple-600" />
        }
      </div>

      <div className={clsx('max-w-[85%] space-y-2', isUser && 'items-end flex flex-col')}>
        <div
          className={clsx(
            'rounded-xl px-4 py-3 text-sm',
            isUser
              ? 'bg-purple-600 text-white'
              : 'bg-white border border-gray-200 text-gray-800'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-sm">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Conflicts */}
        {hasConflicts && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 w-full">
            <div className="flex items-center gap-1 mb-1">
              <AlertTriangle className="w-3 h-3 text-orange-600" />
              <span className="text-xs font-medium text-orange-700">A few things to consider</span>
            </div>
            {message.conflicts.map((c, i) => (
              <p key={i} className="text-xs text-orange-700">{c}</p>
            ))}
          </div>
        )}

        {/* Citations */}
        {hasCitations && (
          <div className="flex items-center gap-1 flex-wrap">
            {/* Local KB citations */}
            {message.citations.filter(c => c.source_type !== 'web').length > 0 && (
              <>
                <BookOpen className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-400">KB:</span>
                {message.citations.filter(c => c.source_type !== 'web').map((c, i) => (
                  <span
                    key={i}
                    className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
                    title={c.doc_title}
                  >
                    {c.doc_title || c.doc_id?.replace(/_/g, ' ')}
                  </span>
                ))}
              </>
            )}
            {/* Web citations */}
            {message.citations.filter(c => c.source_type === 'web').length > 0 && (
              <>
                <Globe className="w-3 h-3 text-blue-400 ml-1" />
                <span className="text-xs text-blue-400">Web:</span>
                {message.citations.filter(c => c.source_type === 'web').map((c, i) => (
                  c.url ? (
                    <a
                      key={i}
                      href={c.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-200 hover:bg-blue-100 transition-colors"
                      title={c.url}
                    >
                      {c.doc_title?.length > 30 ? c.doc_title.slice(0, 30) + '…' : c.doc_title}
                    </a>
                  ) : (
                    <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-200">
                      {c.doc_title}
                    </span>
                  )
                ))}
              </>
            )}
          </div>
        )}

        <span className="text-xs text-gray-400">
          {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ''}
        </span>
      </div>
    </div>
  )
}

function getQuickReplies(workflowState) {
  const replies = {
    intake: [
      "Birthday party for 20 guests, $300 budget at home",
      "Dinner party for 8 guests, $150 budget",
      "Holiday gathering for 30 people",
    ],
    clarification: [
      "No dietary restrictions",
      "We have vegetarian guests",
      "Some guests have nut allergies",
      "Children will be attending",
    ],
    conflict_detection: [
      "Increase budget by $100",
      "Reduce guest count by 5",
      "I'll simplify the menu",
    ],
    planning: [
      "I'm happy with everything, create my plan",
      "Tell me more about the budget breakdown",
      "What decorations do you suggest?",
    ],
    validation: [
      "I'm happy with everything, create my plan",
      "Adjust budget to $400",
      "What about dietary options?",
    ],
    complete: [
      "Update my plan with changes",
      "What's the best entertainment for this event?",
      "Can you suggest more budget savings?",
    ],
  }
  return replies[workflowState] || []
}
