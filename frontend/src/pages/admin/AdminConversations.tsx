import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Bot, User, MessageSquare } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { AIConversation } from '@/types'
import { Modal } from '@/components/ui/Modal'

export const AdminConversations: React.FC = () => {
  const [selectedConv, setSelectedConv] = useState<AIConversation | null>(null)

  const { data: convs = [], isLoading } = useQuery({
    queryKey: ['admin-conversations'],
    queryFn: () => adminService.getConversations(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Clinical Assistant Logs</h1>
        <p className="text-xs text-slate-400">Audit patient AI conversations, triage interactions, and tool calls</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading conversations...</div>
      ) : convs.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No AI chat logs recorded.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {convs.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedConv(c)}
              className="bg-slate-800/80 border border-slate-700 hover:border-slate-500 rounded-2xl p-4 cursor-pointer transition space-y-2"
            >
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-sky-400">{c.patient_name || 'Guest User'}</span>
                <span className="text-[10px] text-slate-400 uppercase bg-slate-900 px-2 py-0.5 rounded">{c.channel}</span>
              </div>
              <p className="text-xs text-slate-300 line-clamp-2">
                {c.messages?.[c.messages.length - 1]?.content || 'Empty conversation'}
              </p>
              <div className="flex justify-between items-center text-[10px] text-slate-500 pt-2 border-t border-slate-700/60">
                <span>{c.messages?.length || 0} messages</span>
                <span>{formatDateTime(c.updated_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <Modal isOpen={!!selectedConv} onClose={() => setSelectedConv(null)} title="AI Conversation Transcript" size="lg">
        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {selectedConv?.messages?.map((m) => {
            const isUser = m.role === 'user' || m.sender === 'patient' || m.sender === 'user'
            const roleName = m.sender || m.role || 'assistant'
            return (
              <div
                key={m.id}
                className={`p-3 rounded-xl text-xs ${
                  isUser ? 'bg-sky-50 text-sky-950 ml-6 border border-sky-100' : 'bg-slate-100 text-slate-800 mr-6 border border-slate-200'
                }`}
              >
                <div className="flex justify-between font-bold mb-1 text-[10px] text-slate-500 uppercase">
                  <span>{roleName}</span>
                  <span>{formatDateTime(m.created_at)}</span>
                </div>
                <p className="whitespace-pre-wrap">{m.content}</p>
              </div>
            )
          })}
        </div>
      </Modal>
    </div>
  )
}
