import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { voiceService } from '@/services/voice'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { Card, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { PhoneCall, Clock, CheckCircle2 } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export const VoiceRequestPage: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const queryClient = useQueryClient()
  const [phone, setPhone] = useState(user?.phone || '')
  const [reason, setReason] = useState('')

  const { data: requests = [], isLoading } = useQuery({
    queryKey: ['my-voice-requests'],
    queryFn: () => voiceService.getMyVoiceRequests(),
  })

  const mutation = useMutation({
    mutationFn: () => voiceService.requestCall({ phone, reason }),
    onSuccess: () => {
      showToast('Voice callback requested! Our clinical desk will call you shortly.', 'success')
      setReason('')
      queryClient.invalidateQueries({ queryKey: ['my-voice-requests'] })
    },
    onError: (err: any) => showToast(err.message || 'Request failed', 'error'),
  })

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Request Doctor Phone Callback</h1>
        <p className="text-xs text-slate-500">Automated queue placement for hospital telephone consultation</p>
      </div>

      <Card className="space-y-4 p-6">
        <CardTitle>New Callback Request</CardTitle>
        <Input
          label="Contact Phone Number"
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+1 555-0199"
          required
        />
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Callback</label>
          <textarea
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Inquiring about prescription change, urgent question about upcoming surgery..."
            className="w-full bg-slate-50 border rounded-xl p-3 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
            required
          />
        </div>
        <Button
          onClick={() => mutation.mutate()}
          isLoading={mutation.isPending}
          disabled={mutation.isPending || !reason.trim()}
          leftIcon={<PhoneCall className="w-4 h-4" />}
        >
          Request Phone Call
        </Button>
      </Card>

      <Card className="space-y-4">
        <CardTitle>My Callback Requests</CardTitle>
        {isLoading ? (
          <p className="text-xs text-slate-400">Loading requests...</p>
        ) : requests.length === 0 ? (
          <p className="text-xs text-slate-500">No active voice callback requests.</p>
        ) : (
          <div className="space-y-3">
            {requests.map((r) => (
              <div key={r.id} className="p-3 bg-slate-50 rounded-xl border flex justify-between items-center text-xs">
                <div>
                  <p className="font-bold text-slate-800">{r.reason}</p>
                  <p className="text-slate-500">{formatDateTime(r.requested_at)}</p>
                </div>
                <Badge variant={r.status === 'completed' ? 'success' : r.status === 'calling' ? 'warning' : 'info'}>
                  {r.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
