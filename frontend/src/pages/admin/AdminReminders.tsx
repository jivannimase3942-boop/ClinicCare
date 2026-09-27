import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { remindersApi } from '@/services/reminders'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { BellRing, Send, Clock, MessageSquare } from 'lucide-react'

export const AdminReminders: React.FC = () => {
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  const { data: remindersData, isLoading } = useQuery({
    queryKey: ['admin-reminders'],
    queryFn: () => remindersApi.getReminders(),
  })

  const dispatchMutation = useMutation({
    mutationFn: (id: string) => remindersApi.dispatchReminder(id),
    onSuccess: () => {
      showToast('success', 'Simulated reminder dispatched to patient!')
      queryClient.invalidateQueries({ queryKey: ['admin-reminders'] })
    },
    onError: () => {
      showToast('error', 'Failed to dispatch reminder')
    },
  })

  const reminders = remindersData?.data || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Follow-Up & Appointment Reminders Queue</h2>
        <p className="text-sm text-slate-400 mt-1">
          Automated WhatsApp & SMS scheduled reminder dispatches for post-consultation and upcoming bookings.
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <BellRing className="w-4 h-4 text-sky-400" />
            Scheduled Reminder Dispatches ({reminders.length})
          </h3>
        </div>

        <div className="divide-y divide-slate-800/60 text-xs">
          {reminders.length === 0 ? (
            <div className="text-center py-10 text-slate-400">
              <BellRing className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="font-semibold text-slate-300">No scheduled reminders in queue</p>
              <p className="text-slate-500 text-xs mt-1">Dispatches for upcoming and completed appointments will appear here.</p>
            </div>
          ) : (
            reminders.map((rem) => (
            <div key={rem.id} className="p-4 hover:bg-slate-800/40 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h4 className="text-sm font-bold text-white">{rem.title}</h4>
                  <p className="text-xs text-slate-400">
                    Patient: {rem.patient_name || 'Patient'} ({rem.patient_phone || 'No Phone'}) • Scheduled: {new Date(rem.scheduled_for).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={rem.status === 'sent_demo' ? 'success' : 'neutral'}>
                    {rem.status === 'sent_demo' ? 'Sent (Demo Dispatched)' : rem.status}
                  </Badge>
                  {rem.status === 'scheduled' && (
                    <button
                      onClick={() => dispatchMutation.mutate(rem.id)}
                      disabled={dispatchMutation.isPending}
                      className="px-2.5 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs flex items-center gap-1"
                    >
                      <Send className="w-3 h-3" /> Trigger Demo Dispatch
                    </button>
                  )}
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-300 font-mono text-[11px]">
                {rem.message}
              </div>
            </div>
          )))}
        </div>
      </div>
    </div>
  )
}
