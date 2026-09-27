import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { PhoneCall, CheckCircle } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export const AdminVoiceCalls: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data: calls = [], isLoading } = useQuery({
    queryKey: ['admin-voice-calls'],
    queryFn: () => adminService.getVoiceCalls(),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminService.updateVoiceCall(id, { status }),
    onSuccess: () => {
      showToast('Voice call status updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-voice-calls'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Voice Callback Queue</h1>
        <p className="text-xs text-slate-400">Manage patient voice requests and telephone consultations</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading queue...</div>
      ) : calls.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No pending voice callback requests.</div>
      ) : (
        <div className="space-y-3">
          {calls.map((c) => (
            <div key={c.id} className="bg-slate-800/80 border border-slate-700 rounded-2xl p-4 flex justify-between items-center text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">{c.patient_name}</span>
                  <span className="text-emerald-400 font-mono font-semibold">{c.phone}</span>
                </div>
                <p className="text-slate-300">Reason: {c.reason}</p>
                <p className="text-slate-500">{formatDateTime(c.requested_at)}</p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={c.status === 'completed' ? 'success' : 'warning'}>{c.status}</Badge>
                {c.status === 'requested' && (
                  <button
                    onClick={() => updateMutation.mutate({ id: c.id, status: 'completed' })}
                    className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl font-semibold"
                  >
                    Mark Done
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
