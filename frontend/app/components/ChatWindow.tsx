'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Sparkles } from 'lucide-react'
import ChartRenderer from './ChartRenderer'
import DataTable from './DataTable'

interface ChartConfig {
  chart_type: 'bar' | 'line' | 'pie' | 'scatter' | 'area'
  title: string
  data: Record<string, unknown>[]
  x_key: string
  y_keys: string[]
  colors?: string[]
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  chart?: ChartConfig
  table_data?: Record<string, unknown>[]
  timestamp: Date
}

interface ChatWindowProps {
  datasetId: string | null
  sessionId: string
}

const SUGGESTED_QUESTIONS = [
  'Which product had the highest revenue?',
  'Show me sales by category as a bar chart',
  'What are the top 5 customers by total spend?',
  'How many orders were placed each month?',
  'What is the average order value?',
  'Which countries have the most orders?',
]

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-tl-sm max-w-xs glass-card">
      <span className="text-lg">🎣</span>
      <div className="flex gap-1">
        <div className="typing-dot w-2 h-2 rounded-full bg-ocean-400" />
        <div className="typing-dot w-2 h-2 rounded-full bg-ocean-400" />
        <div className="typing-dot w-2 h-2 rounded-full bg-ocean-400" />
      </div>
    </div>
  )
}

export default function ChatWindow({ datasetId, sessionId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: datasetId
        ? "🎣 Data loaded! Ask me anything about your dataset in plain English."
        : "👋 Hi! I'm Gradient Fisherman, your AI data assistant.\n\nUpload a CSV file to get started, or try the **Shopify demo data** to see what I can do!\n\nI can answer questions, run calculations, and generate charts — all in plain English. No SQL required! 🐟",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Update welcome message when dataset changes
  useEffect(() => {
    if (datasetId) {
      setMessages(prev => {
        if (prev[0]?.id === 'welcome') {
          return [{
            ...prev[0],
            content: "🎣 Data loaded! Ask me anything about your dataset in plain English.\n\nTry one of the suggested questions below, or ask your own!"
          }, ...prev.slice(1)]
        }
        return prev
      })
    }
  }, [datasetId])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const allMessages = [...messages, userMessage].map(m => ({
        role: m.role,
        content: m.content,
      }))

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: allMessages,
          session_id: sessionId,
          dataset_id: datasetId,
        }),
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.message,
        chart: data.chart,
        table_data: data.table_data,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "🌊 Oops! Something went wrong. Please check that the backend is running and try again.",
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }, [messages, sessionId, datasetId, isLoading])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const formatContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        const boldLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        return <p key={i} className={line === '' ? 'h-2' : ''} dangerouslySetInnerHTML={{ __html: boldLine }} />
      })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
          >
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'max-w-[70%]' : 'w-full'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-base fish-float">🎣</span>
                  <span className="text-xs font-medium text-ocean-400">Gradient Fisherman</span>
                </div>
              )}
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'rounded-tr-sm text-white'
                    : 'rounded-tl-sm glass-card text-slate-200'
                }`}
                style={msg.role === 'user' ? { background: 'linear-gradient(135deg, #0080FF, #0057B3)' } : {}}
              >
                <div className="space-y-1">{formatContent(msg.content)}</div>
              </div>

              {/* Chart */}
              {msg.chart && <ChartRenderer chart={msg.chart} />}

              {/* Table */}
              {msg.table_data && msg.table_data.length > 0 && (
                <DataTable data={msg.table_data} />
              )}

              <p className="text-xs text-slate-600 mt-1 px-1">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start message-enter">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-base fish-float">🎣</span>
                <span className="text-xs font-medium text-ocean-400">Gradient Fisherman</span>
              </div>
              <TypingIndicator />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions */}
      {datasetId && messages.length <= 2 && (
        <div className="px-4 pb-2">
          <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Suggested questions
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.slice(0, 4).map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                disabled={isLoading}
                className="text-xs px-3 py-1.5 rounded-full transition-all hover:scale-105 disabled:opacity-50"
                style={{
                  background: 'rgba(0,128,255,0.15)',
                  border: '1px solid rgba(0,128,255,0.3)',
                  color: '#90E0EF',
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="p-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
        <div
          className="flex items-end gap-3 rounded-xl p-3"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(0,128,255,0.25)' }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={datasetId ? "Ask about your data… (Enter to send)" : "Upload a CSV to start asking questions…"}
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 resize-none outline-none leading-relaxed"
            style={{ maxHeight: '120px' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-all hover:scale-110 disabled:opacity-30 disabled:hover:scale-100"
            style={{ background: 'linear-gradient(135deg, #0080FF, #0057B3)' }}
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-2 text-center">
          Powered by DigitalOcean Gradient™ AI · {datasetId ? 'Dataset loaded ✓' : 'No dataset loaded'}
        </p>
      </div>
    </div>
  )
}
