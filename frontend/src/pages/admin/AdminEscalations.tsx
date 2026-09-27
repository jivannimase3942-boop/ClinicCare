import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { AlertOctagon, Phone, User, CheckCircle2 } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export const AdminEscalations: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data: escalations = [], isLoading } = useQuery({
    queryKey: ['admin-escalations'],
    queryFn: () => adminService.getEscalations(),
  })

  const resolveMutation = useMutation({
    mutationFn: (id: string) =>
      adminService.updateEscalation(id, { status: 'resolved', admin_notes: 'Resolved by front desk staff.' }),
    onSuccess: () => {
      showToast('Escalation marked as resolved', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-escalations'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Front-Desk & Emergency Escalations</h1>
        <p className="text-xs text-slate-400">Interventions triggered by medical AI, patients, or front-desk triage</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading escalations...</div>
      ) : escalations.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No active escalations. All patient queries are clear!</div>
      ) : (
        <div className="space-y-3">
          {escalations.map((esc) => (
            <div key={esc.id} className="bg-slate-800/90 border border-slate-700 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center gap-2">
                  <Badge variant={esc.priority === 'urgent' ? 'danger' : esc.priority === 'high' ? 'warning' : 'info'}>
                    {esc.priority} Priority
                  </Badge>
                  <span className="text-xs text-slate-400">Reason: <strong className="text-white uppercase">{esc.reason.replace('_', ' ')}</strong></span>
                  <span className="text-[10px] text-slate-500">• {formatDateTime(esc.created_at)}</span>
                </div>
                <p className="text-sm font-semibold text-slate-100">{esc.message}</p>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><User className="w-3.5 h-3.5 text-sky-400" /> Patient: {esc.patient_name}</span>
                  {esc.patient_phone && <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5 text-emerald-400" /> {esc.patient_phone}</span>}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant={esc.status === 'resolved' ? 'success' : 'danger'}>{esc.status}</Badge>
                {esc.status !== 'resolved' && (
                  <button
                    onClick={() => resolveMutation.mutate(esc.id)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Resolve
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
