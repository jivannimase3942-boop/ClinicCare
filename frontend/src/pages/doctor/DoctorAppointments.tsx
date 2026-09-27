import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorPortalService } from '@/services/doctor_portal'
import { useToast } from '@/context/ToastContext'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/lib/utils'

export const DoctorAppointments: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['doctor-appointments'],
    queryFn: () => doctorPortalService.getAppointments(),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      doctorPortalService.updateAppointmentStatus(id, status),
    onSuccess: () => {
      showToast('Consultation status updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Consultations</h1>
        <p className="text-xs text-slate-500">Manage patient visits, complete checkups, and record notes</p>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">Loading consultations...</div>
      ) : appointments.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-xs">No assigned consultations.</div>
      ) : (
        <div className="space-y-3">
          {appointments.map((a) => (
            <Card key={a.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900 text-sm">{a.patient_name}</h3>
                  <Badge variant={a.status === 'confirmed' ? 'success' : a.status === 'completed' ? 'primary' : 'default'}>
                    {a.status}
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 font-medium">{formatDate(a.appointment_date)} at {a.appointment_time}</p>
                {a.reason && <p className="text-xs text-slate-500">Chief complaint: {a.reason}</p>}
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                {a.status === 'confirmed' && (
                  <>
                    <Button size="sm" onClick={() => updateMutation.mutate({ id: a.id, status: 'completed' })}>
                      Mark Completed
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => updateMutation.mutate({ id: a.id, status: 'no_show' })}>
                      No Show
                    </Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
