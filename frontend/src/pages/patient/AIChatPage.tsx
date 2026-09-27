import React, { useState, useRef, useEffect } from 'react'
import { aiService } from '@/services/ai'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Send, Bot, User, Sparkles, AlertTriangle, PhoneCall, Loader2, RefreshCw } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  isEmergency?: boolean
  escalated?: boolean
  timestamp: string
}

const QUICK_PROMPTS = [
  'Tell me about cetirizine',
  'Who are the available doctors?',
  'How do I book an appointment?',
  'What departments are available?',
  'Which blood group is available?',
  'Where is the blood bank?',
  'Request an ambulance',
  'What are the clinic timings?',
  'Show available ambulance information',
  'Show emergency requests',
  'How can I cancel my appointment?',
]


export const AIChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your ClinicCare Hospital AI Clinical Assistant. You can ask about medicines, check doctor availability, book appointments, check report statuses, or request a voice callback. How can I assist you?',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim()
    if (!text || isLoading) return

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((p) => [...p, userMsg])
    if (!textToSend) setInput('')
    setIsLoading(true)

    try {
      const res = await aiService.sendMessage({ message: text, conversation_id: conversationId })
      if (res.conversation_id) setConversationId(res.conversation_id)
      const assistantText = res.response || (res as any).reply || 'Thank you for reaching out. How else can I assist you?'
      setMessages((p) => [
        ...p,
        {
          id: Math.random().toString(36).substring(7),
          role: 'assistant',
          content: assistantText,
          isEmergency: Boolean(res.is_emergency),
          escalated: Boolean(res.escalation_triggered),
          timestamp: new Date().toISOString(),
        },
      ])
    } catch (err: any) {
      const errorMsg = err?.message || 'Sorry, I encountered an issue reaching hospital services. Please try again.'
      setMessages((p) => [
        ...p,
        {
          id: Math.random().toString(36).substring(7),
          role: 'assistant',
          content: errorMsg,
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setConversationId(undefined)
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I am your ClinicCare Hospital AI Clinical Assistant. You can ask about medicines, check doctor availability, book appointments, check report statuses, or request a voice callback. How can I assist you?',
        timestamp: new Date().toISOString(),
      },
    ])
  }

  return (
    <div className="max-w-4xl mx-auto space-y-3 h-[calc(100vh-7rem)] flex flex-col">
      <div className="flex justify-between items-center pb-2 border-b">
        <h1 className="text-xl font-bold flex items-center gap-2 text-slate-800">
          <Sparkles className="w-5 h-5 text-sky-600" /> ClinicCare AI Assistant
        </h1>
        <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5 text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Restart Chat
        </Button>
      </div>

      <div className="bg-amber-50 border border-amber-200 p-2.5 rounded-xl text-xs text-amber-800 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>For life-threatening medical emergencies, immediately call 911 / 112 or proceed to the nearest Emergency OPD.</span>
      </div>

      <Card className="flex-1 flex flex-col p-4 min-h-0 bg-slate-50">
        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-3.5 text-sm leading-relaxed ${
                msg.role === 'user' ? 'bg-sky-600 text-white rounded-br-none' : 'bg-white text-slate-800 border rounded-bl-none shadow-sm'
              } ${msg.isEmergency ? 'border-2 border-rose-500 bg-rose-50' : ''}`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.escalated && (
                  <div className="mt-1.5 pt-1.5 border-t flex items-center gap-1 text-xs text-amber-700">
                    <PhoneCall className="w-3.5 h-3.5" /> Front desk team notified.
                  </div>
                )}
                <div className={`mt-1 text-[10px] ${msg.role === 'user' ? 'text-sky-200 text-right' : 'text-slate-400'}`}>
                  {formatDateTime(msg.timestamp)}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="text-xs text-slate-500 flex items-center gap-2 bg-white p-2.5 rounded-xl border border-slate-200 w-fit shadow-sm">
              <Loader2 className="w-4 h-4 animate-spin text-sky-600" /> ClinicCare AI is formulating a response...
            </div>
          )}
          <div ref={endRef} />
        </div>

        {messages.length <= 2 && (
          <div className="py-2 flex gap-1.5 overflow-x-auto text-xs no-scrollbar">
            {QUICK_PROMPTS.map((qp, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(qp)}
                disabled={isLoading}
                className="whitespace-nowrap px-3 py-1.5 bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 border border-slate-200 rounded-full transition text-xs shrink-0 disabled:opacity-50 cursor-pointer"
              >
                {qp}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2 pt-2 border-t bg-white p-2 rounded-xl border border-slate-200 shadow-sm">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question (e.g. tell me about cetirizine, check slots, doctors, reports)..."
            className="flex-1 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 transition"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </Card>
    </div>
  )
}
