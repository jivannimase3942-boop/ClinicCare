import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/lib/utils'

export const AdminAppointments: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [statusFilter, setStatusFilter] = useState('')

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['admin-appointments', statusFilter],
    queryFn: () => adminService.getAppointments({ status: statusFilter || undefined }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminService.updateAppointmentStatus(id, status),
    onSuccess: () => {
      showToast('Status updated successfully', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-appointments'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError: (err: any) => showToast(err.message || 'Update failed', 'error'),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">All Hospital Appointments</h1>
          <p className="text-xs text-slate-400">Total appointments: {appointments.length}</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-800 text-white border border-slate-700 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-sky-500"
        >
          <option value="">All Statuses</option>
          <option value="confirmed">Confirmed</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No Show</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading appointments...</div>
      ) : appointments.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No appointments found.</div>
      ) : (
        <div className="bg-slate-800/80 rounded-2xl border border-slate-700 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-700">
              <tr>
                <th className="p-4">Patient</th>
                <th className="p-4">Doctor & Dept</th>
                <th className="p-4">Date & Time</th>
                <th className="p-4">Reason</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60">
              {appointments.map((a) => (
                <tr key={a.id} className="hover:bg-slate-700/30 transition">
                  <td className="p-4 font-bold text-white">{a.patient_name}</td>
                  <td className="p-4">
                    <p className="font-semibold text-slate-200">{a.doctor_name}</p>
                    <p className="text-[10px] text-slate-400">{a.department_name}</p>
                  </td>
                  <td className="p-4">
                    <p className="font-medium text-slate-200">{formatDate(a.appointment_date)}</p>
                    <p className="text-[10px] text-sky-400">{a.appointment_time}</p>
                  </td>
                  <td className="p-4 text-slate-400 max-w-[200px] truncate">{a.reason || 'General Checkup'}</td>
                  <td className="p-4">
                    <Badge variant={a.status === 'confirmed' ? 'success' : a.status === 'completed' ? 'primary' : 'danger'}>
                      {a.status}
                    </Badge>
                  </td>
                  <td className="p-4 text-right space-x-1.5">
                    {a.status === 'confirmed' && (
                      <>
                        <button
                          onClick={() => updateMutation.mutate({ id: a.id, status: 'completed' })}
                          className="px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30 hover:bg-emerald-500/30 font-semibold"
                        >
                          Complete
                        </button>
                        <button
                          onClick={() => updateMutation.mutate({ id: a.id, status: 'cancelled' })}
                          className="px-2 py-1 bg-rose-500/20 text-rose-300 rounded border border-rose-500/30 hover:bg-rose-500/30 font-semibold"
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
