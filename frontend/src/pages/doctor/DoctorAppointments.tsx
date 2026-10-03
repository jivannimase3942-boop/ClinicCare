import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorPortalService } from '@/services/doctor_portal'
import { appointmentService } from '@/services/appointments'
import { useToast } from '@/context/ToastContext'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/lib/utils'
import { Volume2, PlayCircle, CheckCircle, SkipForward, Stethoscope } from 'lucide-react'

export const DoctorAppointments: React.FC = () => {
  const navigate = useNavigate()
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

  const queueMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: any }) =>
      appointmentService.updateQueue(id, status),
    onSuccess: () => {
      showToast('OPD queue updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] })
    },
    onError: (err: any) => showToast(err.message || 'Queue transition failed', 'error')
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Consultations & OPD Queue</h1>
        <p className="text-xs text-slate-500">Manage patient visits, advance queue tokens, complete checkups, and record notes</p>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">Loading consultations...</div>
      ) : appointments.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-xs">No assigned consultations.</div>
      ) : (
        <div className="space-y-3">
          {appointments.map((a) => (
            <Card key={a.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-slate-900 text-sm">{a.patient_name}</h3>
                  {a.token_number && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-teal-100 text-teal-800">
                      Token #{a.token_number}
                    </span>
                  )}
                  {a.queue_status ? (
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                      a.queue_status === 'IN_CONSULTATION' ? 'bg-amber-100 text-amber-800' :
                      a.queue_status === 'WAITING' ? 'bg-blue-100 text-blue-800' :
                      a.queue_status === 'CALLED' ? 'bg-purple-100 text-purple-800' :
                      a.queue_status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
                    }`}>
                      OPD: {a.queue_status.replace('_', ' ')}
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-500">
                      Not Checked In
                    </span>
                  )}
                  <Badge variant={a.status === 'confirmed' ? 'success' : a.status === 'completed' ? 'primary' : 'default'}>
                    {a.status}
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 font-medium">{formatDate(a.appointment_date)} at {a.appointment_time}</p>
                {a.reason && <p className="text-xs text-slate-500">Chief complaint: {a.reason}</p>}
              </div>

              <div className="flex items-center gap-2 flex-wrap self-end md:self-center">
                {/* Queue Controls */}
                {a.queue_status === 'WAITING' && (
                  <Button
                    size="sm"
                    className="bg-purple-600 hover:bg-purple-700"
                    leftIcon={<Volume2 className="w-3.5 h-3.5" />}
                    onClick={() => queueMutation.mutate({ id: a.id, status: 'CALLED' })}
                    isLoading={queueMutation.isPending}
                  >
                    Call Patient
                  </Button>
                )}
                {a.queue_status === 'CALLED' && (
                  <Button
                    size="sm"
                    className="bg-amber-600 hover:bg-amber-700"
                    leftIcon={<PlayCircle className="w-3.5 h-3.5" />}
                    onClick={() => queueMutation.mutate({ id: a.id, status: 'IN_CONSULTATION' })}
                    isLoading={queueMutation.isPending}
                  >
                    Start OPD
                  </Button>
                )}
                {a.queue_status === 'IN_CONSULTATION' && (
                  <Button
                    size="sm"
                    className="bg-emerald-600 hover:bg-emerald-700"
                    leftIcon={<CheckCircle className="w-3.5 h-3.5" />}
                    onClick={() => queueMutation.mutate({ id: a.id, status: 'COMPLETED' })}
                    isLoading={queueMutation.isPending}
                  >
                    Finish OPD
                  </Button>
                )}
                {(a.queue_status === 'WAITING' || a.queue_status === 'CALLED') && (
                  <Button
                    variant="outline"
                    size="sm"
                    leftIcon={<SkipForward className="w-3.5 h-3.5" />}
                    onClick={() => queueMutation.mutate({ id: a.id, status: 'SKIPPED' })}
                    isLoading={queueMutation.isPending}
                  >
                    Skip
                  </Button>
                )}

                {/* Clinical Encounter Action */}
                <Button
                  size="sm"
                  variant="outline"
                  className="border-teal-600 text-teal-800 hover:bg-teal-50"
                  leftIcon={<Stethoscope className="w-3.5 h-3.5 text-teal-600" />}
                  onClick={() => navigate(`/doctor/consultation/${a.id}`)}
                >
                  Clinical Notes
                </Button>

                {/* Legacy Status Action */}
                {a.status === 'confirmed' && !a.queue_status && (
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
