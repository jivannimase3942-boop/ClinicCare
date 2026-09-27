import React, { useState, useRef, useEffect } from 'react'
import { aiService } from '@/services/ai'
import { X, Send, Sparkles, Bot, User, AlertTriangle, PhoneCall, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { formatDateTime } from '@/lib/utils'

interface ChatMsg {
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
  'Which blood group is available?',
  'Where is the blood bank?',
  'Request an ambulance',
  'What are the clinic timings?',
  'Show emergency requests',
]


export const AIChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your ClinicCare Hospital AI Assistant. How can I help you today? You can ask about medicines, find specialists, check open slots, or request a call.',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isOpen])

  const handleSend = async (messageOverride?: string) => {
    const textToSend = (messageOverride || input).trim()
    if (!textToSend || isLoading) return

    const userMsg: ChatMsg = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content: textToSend,
      timestamp: new Date().toISOString(),
    }
    setMessages((p) => [...p, userMsg])
    if (!messageOverride) setInput('')
    setIsLoading(true)

    try {
      const res = await aiService.sendMessage({ message: textToSend, conversation_id: conversationId })
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
      const errorMsg = err?.message || 'AI service is temporarily unavailable. Please try again or contact the front desk.'
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
        content: 'Hello! I am your CarePulse Hospital AI Assistant. How can I help you today? You can ask about medicines, find specialists, check open slots, or request a call.',
        timestamp: new Date().toISOString(),
      },
    ])
  }

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-2xl bg-sky-600 text-white font-semibold shadow-xl hover:scale-105 transition active:scale-95 cursor-pointer"
          aria-label="Open CarePulse AI Assistant"
        >
          <Sparkles className="w-5 h-5" />
          <span className="text-sm">CarePulse AI</span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden w-[360px] sm:w-[410px] h-[540px]">
          <div className="bg-sky-700 p-3 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-sky-200" />
              <div>
                <h4 className="font-bold text-sm leading-none">CarePulse AI Assistant</h4>
                <span className="text-[10px] text-sky-200">Online • Hospital Orchestration</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={handleReset} title="Restart chat" className="p-1.5 hover:bg-white/10 rounded-lg transition text-sky-100 hover:text-white">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => setIsOpen(false)} title="Close chat" className="p-1.5 hover:bg-white/10 rounded-lg transition text-sky-100 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="bg-amber-50 px-3 py-1.5 text-[11px] text-amber-800 flex items-center gap-1.5 border-b border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>AI does not prescribe. For life-threatening emergencies call 911 / 112.</span>
          </div>

          <div className="flex-1 p-3 overflow-y-auto space-y-2.5 bg-slate-50 text-xs sm:text-sm">
            {messages.map((m) => (
              <div key={m.id} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-3 leading-relaxed ${m.role === 'user' ? 'bg-sky-600 text-white rounded-br-none shadow-sm' : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'} ${m.isEmergency ? 'border-2 border-rose-500 bg-rose-50 text-rose-950 font-medium' : ''}`}>
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.escalated && (
                    <div className="mt-2 pt-1.5 border-t border-amber-300 text-[11px] text-amber-800 font-medium flex items-center gap-1.5">
                      <PhoneCall className="w-3.5 h-3.5 text-amber-600" /> Front desk team notified & active.
                    </div>
                  )}
                  <div className={`mt-1 text-[9px] ${m.role === 'user' ? 'text-sky-200 text-right' : 'text-slate-400'}`}>
                    {formatDateTime(m.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 bg-white p-2.5 rounded-xl border border-slate-200 w-fit shadow-sm">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-600" /> CarePulse AI is formulating a response...
              </div>
            )}
            <div ref={endRef} />
          </div>

          {messages.length <= 2 && (
            <div className="px-2.5 py-1.5 bg-slate-100 border-t border-slate-200 flex gap-1.5 overflow-x-auto text-[11px] no-scrollbar">
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(qp)}
                  disabled={isLoading}
                  className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 border border-slate-200 rounded-full transition text-[11px] shrink-0 disabled:opacity-50"
                >
                  {qp}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="p-2.5 bg-white border-t border-slate-200 flex gap-2 items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about cetirizine, doctors, slots..."
              className="flex-1 bg-slate-50 text-xs sm:text-sm px-3.5 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 transition"
              disabled={isLoading}
            />
            <Button type="submit" size="sm" disabled={isLoading || !input.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      )}
    </>
  )
}
