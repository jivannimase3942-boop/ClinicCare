import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { remindersApi } from '@/services/reminders'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { BellRing, Clock, Send, CheckCircle2, AlertCircle, MessageSquare } from 'lucide-react'

export const RemindersPage: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()
  const patientId = user?.patient_profile?.id

  const { data, isLoading } = useQuery({
    queryKey: ['my-reminders', patientId],
    queryFn: () => (patientId ? remindersApi.getReminders({ patient_id: patientId }) : Promise.resolve({ success: true, data: [] })),
    enabled: !!patientId,
  })

  const dispatchMutation = useMutation({
    mutationFn: (id: string) => remindersApi.dispatchReminder(id),
    onSuccess: () => {
      showToast('success', 'Simulated reminder dispatched to patient channel!')
      queryClient.invalidateQueries({ queryKey: ['my-reminders'] })
    },
    onError: () => {
      showToast('error', 'Failed to dispatch reminder')
    },
  })

  const reminders = data?.data || []

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent_demo':
        return <Badge variant="success">Sent (Demo Dispatched)</Badge>
      case 'pending':
        return <Badge variant="warning">Pending Scan</Badge>
      case 'failed':
        return <Badge variant="danger">Failed</Badge>
      default:
        return <Badge variant="neutral">Scheduled</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-700 to-sky-700 rounded-2xl p-6 text-white shadow-lg flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 border border-white/20">
            <BellRing className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-black tracking-tight">Appointment & Follow-Up Reminders</h2>
            <p className="text-xs text-indigo-100 mt-0.5">
              Automated reminders and notifications scheduled for your care plan.
            </p>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600" />
            Scheduled & Past Notifications ({reminders.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          {reminders.length === 0 ? (
            <div className="text-center py-12">
              <BellRing className="w-12 h-12 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-bold text-slate-700">No scheduled reminders</p>
              <p className="text-xs text-slate-500 mt-1">Reminders for upcoming consultations will be scheduled here.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reminders.map((rem) => (
                <div key={rem.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{rem.title}</h4>
                      <p className="text-xs text-slate-500">Scheduled: {new Date(rem.scheduled_for).toLocaleString()} • Channel: {rem.channel}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(rem.status)}
                      {rem.status === 'scheduled' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => dispatchMutation.mutate(rem.id)}
                          isLoading={dispatchMutation.isPending}
                          leftIcon={<Send className="w-3.5 h-3.5" />}
                          className="text-xs py-1"
                        >
                          Simulate Dispatch
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="bg-white p-3 rounded-lg border border-slate-200/80 text-xs text-slate-700 font-medium">
                    <MessageSquare className="w-3.5 h-3.5 text-indigo-500 inline mr-1.5" />
                    {rem.message}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
