"use client"

import { useState, useRef, useEffect } from "react"
import { useSession } from "next-auth/react"
import { runAgentTask } from "@/lib/api"
import { Bot, Send, User, Loader2, Zap } from "lucide-react"

interface Message {
  role: "user" | "agent"
  content: string
  timestamp: Date
}

const QUICK_TASKS = [
  "Post today's content on all 3 platforms",
  "Generate a LinkedIn thought leadership post about AI automation trends in Nigeria",
  "Create a Twitter tip about saving time with WhatsApp Business automation",
  "Show me an analytics summary",
  "Create a 14-day campaign targeting Lagos SMEs interested in sales automation",
  "Generate an Instagram before/after post about a retail client we automated",
]

export function AgentClient() {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content:
        "Hello! I'm your autonomous marketing agent for Primemash Technologies.\n\n" +
        "I can generate and publish content to LinkedIn, X (Twitter), and Instagram, " +
        "create marketing campaigns with full content calendars, and report on performance.\n\n" +
        "What would you like me to do?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function sendMessage(task: string) {
    if (!task.trim() || !session?.backendToken || loading) return

    const userMsg: Message = { role: "user", content: task, timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const res = await runAgentTask(session.backendToken, task)
      const agentMsg: Message = {
        role: "agent",
        content: res.result ?? res.error ?? "Task completed.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, agentMsg])
    } catch (err: unknown) {
      const errMsg: Message = {
        role: "agent",
        content: `Error: ${err instanceof Error ? err.message : "Something went wrong"}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Bot className="h-6 w-6 text-brand-600" />
          Marketing Agent
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Give the agent team any marketing task — content creation, publishing, campaigns, analytics
        </p>
      </div>

      {/* Quick tasks */}
      <div className="flex flex-wrap gap-2">
        {QUICK_TASKS.map((task) => (
          <button
            key={task}
            onClick={() => sendMessage(task)}
            disabled={loading}
            className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-gray-600 hover:border-brand-400 hover:text-brand-700 transition-colors disabled:opacity-50"
          >
            <Zap className="inline h-3 w-3 mr-1" />
            {task.length > 50 ? task.slice(0, 50) + "…" : task}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "agent" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100">
                <Bot className="h-4 w-4 text-brand-600" />
              </div>
            )}
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-tr-sm"
                  : "bg-gray-50 text-gray-800 rounded-tl-sm border border-gray-100"
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              <p
                className={`mt-1 text-xs ${
                  msg.role === "user" ? "text-brand-200" : "text-gray-400"
                }`}
              >
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
            {msg.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200">
                <User className="h-4 w-4 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100">
              <Bot className="h-4 w-4 text-brand-600" />
            </div>
            <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-gray-100 bg-gray-50 px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
              <span className="text-sm text-gray-500">Agents working…</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
          placeholder="Give the agent team a task… e.g. Post today's LinkedIn content"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-primary px-5 py-3"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </form>
    </div>
  )
}
