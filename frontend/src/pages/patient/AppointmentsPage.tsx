import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appointmentService } from '@/services/appointments'
import { doctorService } from '@/services/doctors'
import { useToast } from '@/context/ToastContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Calendar, Clock, Stethoscope, CalendarClock } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { Appointment } from '@/types'

export const AppointmentsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [filter, setFilter] = useState('all')
  const [cancelModal, setCancelModal] = useState<Appointment | null>(null)
  const [cancelReason, setCancelReason] = useState('')

  // Reschedule state
  const [rescheduleModal, setRescheduleModal] = useState<Appointment | null>(null)
  const [rescheduleDate, setRescheduleDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  })
  const [rescheduleTime, setRescheduleTime] = useState('')

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['patient-appointments'],
    queryFn: () => appointmentService.getMyAppointments(),
  })

  // Fetch slots for selected doctor in reschedule modal
  const { data: rescheduleSlots = [], isLoading: loadingSlots } = useQuery({
    queryKey: ['reschedule-slots', rescheduleModal?.doctor_id, rescheduleDate],
    queryFn: () =>
      rescheduleModal?.doctor_id && rescheduleDate
        ? doctorService.getDoctorSlots(rescheduleModal.doctor_id, rescheduleDate)
        : Promise.resolve([]),
    enabled: !!rescheduleModal?.doctor_id && !!rescheduleDate,
  })

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      appointmentService.cancelAppointment(id, { cancellation_reason: reason }),
    onSuccess: () => {
      showToast('Appointment cancelled successfully', 'success')
      queryClient.invalidateQueries({ queryKey: ['patient-appointments'] })
      setCancelModal(null)
    },
    onError: (err: any) => showToast(err.message || 'Failed to cancel', 'error'),
  })

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, new_date, new_time }: { id: string; new_date: string; new_time: string }) =>
      appointmentService.rescheduleAppointment(id, { new_date, new_time }),
    onSuccess: () => {
      showToast('Appointment rescheduled successfully', 'success')
      queryClient.invalidateQueries({ queryKey: ['patient-appointments'] })
      setRescheduleModal(null)
    },
    onError: (err: any) => showToast(err.message || 'Failed to reschedule', 'error'),
  })

  const filtered = appointments.filter((a) => {
    if (filter === 'upcoming') return a.status === 'confirmed' || a.status === 'pending'
    if (filter === 'completed') return a.status === 'completed'
    if (filter === 'cancelled') return a.status === 'cancelled'
    return true
  })

  const availableRescheduleSlots = rescheduleSlots.filter((s) => !s.is_booked)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">My Appointments</h1>
          <p className="text-xs text-slate-500">View and manage your scheduled consultations</p>
        </div>
        <div className="flex gap-1 bg-white p-1 rounded-xl border">
          {['all', 'upcoming', 'completed', 'cancelled'].map((tab) => (
            <button key={tab} onClick={() => setFilter(tab)} className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize ${filter === tab ? 'bg-sky-600 text-white' : 'text-slate-600'}`}>{tab}</button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center text-slate-500">No appointments found.</div>
      ) : (
        <div className="space-y-3">
          {filtered.map((appt) => (
            <Card key={appt.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 gap-4">
              <div className="flex items-start gap-3">
                <Stethoscope className="w-6 h-6 text-sky-600 mt-1" />
                <div>
                  <h3 className="font-bold text-slate-900">{appt.doctor_name || 'Doctor'}</h3>
                  <p className="text-xs text-slate-500">{appt.department_name}</p>
                  <p className="text-xs text-slate-600 mt-1 font-medium">{formatDate(appt.appointment_date)} at {appt.appointment_time}</p>
                  {appt.reason && <p className="text-xs text-slate-400 mt-0.5">Reason: {appt.reason}</p>}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={appt.status === 'confirmed' ? 'success' : appt.status === 'cancelled' ? 'danger' : 'default'}>{appt.status}</Badge>
                {appt.status === 'confirmed' && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      leftIcon={<CalendarClock className="w-3.5 h-3.5" />}
                      onClick={() => {
                        setRescheduleModal(appt)
                        setRescheduleTime('')
                      }}
                    >
                      Reschedule
                    </Button>
                    <Button variant="danger" size="sm" onClick={() => setCancelModal(appt)}>Cancel</Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Cancel Modal */}
      <Modal isOpen={!!cancelModal} onClose={() => setCancelModal(null)} title="Cancel Appointment">
        <div className="space-y-4">
          <p className="text-xs text-slate-600">Are you sure you want to cancel your consultation?</p>
          <Input label="Reason" value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} placeholder="Reason for cancellation" />
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setCancelModal(null)}>Back</Button>
            <Button variant="danger" size="sm" isLoading={cancelMutation.isPending} onClick={() => cancelModal && cancelMutation.mutate({ id: cancelModal.id, reason: cancelReason })}>Confirm</Button>
          </div>
        </div>
      </Modal>

      {/* Reschedule Modal */}
      <Modal isOpen={!!rescheduleModal} onClose={() => setRescheduleModal(null)} title="Reschedule Appointment">
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            Rescheduling consultation with <strong>{rescheduleModal?.doctor_name}</strong>
          </p>

          <Input
            type="date"
            label="New Date"
            value={rescheduleDate}
            min={new Date().toISOString().split('T')[0]}
            onChange={(e) => {
              setRescheduleDate(e.target.value)
              setRescheduleTime('')
            }}
            required
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">Select New Time Slot</label>
            {loadingSlots ? (
              <p className="text-xs text-slate-400">Loading slots...</p>
            ) : availableRescheduleSlots.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
                No slots available on this date for this doctor. Please pick another date.
              </p>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                {availableRescheduleSlots.map((s) => (
                  <button
                    type="button"
                    key={s.id}
                    onClick={() => setRescheduleTime(s.start_time)}
                    className={`py-2 text-xs font-semibold rounded-xl border transition ${
                      rescheduleTime === s.start_time
                        ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                        : 'bg-white text-slate-700 hover:bg-slate-50 border-slate-200'
                    }`}
                  >
                    {s.start_time}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setRescheduleModal(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={!rescheduleDate || !rescheduleTime || rescheduleMutation.isPending}
              isLoading={rescheduleMutation.isPending}
              onClick={() =>
                rescheduleModal &&
                rescheduleMutation.mutate({
                  id: rescheduleModal.id,
                  new_date: rescheduleDate,
                  new_time: rescheduleTime,
                })
              }
            >
              Confirm Reschedule
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
