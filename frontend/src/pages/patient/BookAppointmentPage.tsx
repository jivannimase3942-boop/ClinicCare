import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { doctorService } from '@/services/doctors'
import { appointmentService } from '@/services/appointments'
import { useToast } from '@/context/ToastContext'
import { Card, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { CheckCircle2 } from 'lucide-react'

export const BookAppointmentPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const initialDoctorId = searchParams.get('doctor_id') || ''
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [selectedDept, setSelectedDept] = useState('')
  const [selectedDoctorId, setSelectedDoctorId] = useState(initialDoctorId)
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split('T')[0]
  })
  const [selectedTime, setSelectedTime] = useState('')
  const [appointmentType, setAppointmentType] = useState('NEW_CONSULTATION')
  const [reason, setReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isWaitlisting, setIsWaitlisting] = useState(false)

  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => doctorService.getDepartments(),
  })

  const { data: doctors = [] } = useQuery({
    queryKey: ['doctors', selectedDept],
    queryFn: () => doctorService.getDoctors({ department_id: selectedDept || undefined }),
  })

  const { data: slots = [], isLoading: loadingSlots } = useQuery({
    queryKey: ['doctor-slots', selectedDoctorId, selectedDate],
    queryFn: () => doctorService.getDoctorSlots(selectedDoctorId, selectedDate),
    enabled: !!selectedDoctorId && !!selectedDate,
  })

  useEffect(() => {
    if (initialDoctorId) {
      setSelectedDoctorId(initialDoctorId)
    }
  }, [initialDoctorId])

  useEffect(() => {
    if (initialDoctorId && doctors.length > 0 && !selectedDept) {
      const doc = doctors.find((d) => d.id === initialDoctorId)
      if (doc) setSelectedDept(doc.department_id)
    }
  }, [initialDoctorId, doctors, selectedDept])

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDoctorId || !selectedDate || !selectedTime) return
    setIsSubmitting(true)
    try {
      await appointmentService.createAppointment({
        doctor_id: selectedDoctorId,
        appointment_date: selectedDate,
        appointment_time: selectedTime,
        appointment_type: appointmentType as any,
        reason: reason || undefined,
      })
      await queryClient.invalidateQueries({ queryKey: ['patient-appointments'] })
      showToast('Appointment confirmed successfully!', 'success')
      navigate('/patient/appointments')
    } catch (err: any) {
      showToast(err.message || 'Booking failed', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleJoinWaitlist = async () => {
    if (!selectedDoctorId || !selectedDate) return
    setIsWaitlisting(true)
    try {
      await appointmentService.joinWaitlist({
        doctor_id: selectedDoctorId,
        desired_date: selectedDate,
        notes: reason || 'Slots full, requested waitlist',
      })
      showToast('Successfully placed on the doctor waitlist! Reception will notify you when a slot opens.', 'success')
    } catch (err: any) {
      showToast(err.message || 'Failed to join waitlist', 'error')
    } finally {
      setIsWaitlisting(false)
    }
  }

  const availableSlots = slots.filter((s) => !s.is_booked)

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Book Doctor Appointment</h1>
      <form onSubmit={handleBook} className="space-y-6">
        <Card className="space-y-4">
          <CardTitle>1. Select Doctor & Visit Type</CardTitle>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Select label="Department" value={selectedDept} onChange={(e) => { setSelectedDept(e.target.value); setSelectedDoctorId(''); setSelectedTime(''); }}>
              <option value="">All Departments</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </Select>
            <Select label="Doctor" value={selectedDoctorId} onChange={(e) => { setSelectedDoctorId(e.target.value); setSelectedTime(''); }} required>
              <option value="">Select Doctor...</option>
              {doctors.map((doc) => <option key={doc.id} value={doc.id}>{doc.full_name} ({doc.specialization})</option>)}
            </Select>
            <Select label="Consultation Type" value={appointmentType} onChange={(e) => setAppointmentType(e.target.value)} required>
              <option value="NEW_CONSULTATION">New Consultation</option>
              <option value="FOLLOW_UP">Follow-up Visit</option>
              <option value="PROCEDURE">Procedure / Treatment</option>
              <option value="TELECONSULTATION">Teleconsultation Ready</option>
              <option value="EMERGENCY">Urgent / Priority</option>
            </Select>
          </div>
        </Card>

        {selectedDoctorId && (
          <Card className="space-y-4">
            <CardTitle>2. Select Date & Slot</CardTitle>
            <Input type="date" label="Date" value={selectedDate} min={new Date().toISOString().split('T')[0]} onChange={(e) => { setSelectedDate(e.target.value); setSelectedTime(''); }} required />
            <div>
              <p className="text-xs font-semibold mb-2">Available Slots ({selectedDate})</p>
              {loadingSlots ? (
                <p className="text-xs text-slate-400">Loading slots...</p>
              ) : availableSlots.length === 0 ? (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
                  <p className="text-xs font-medium text-amber-800">
                    No open booking slots available for this doctor on {selectedDate}. All standard slots are filled or the doctor has scheduled leave.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="border-amber-300 text-amber-900 hover:bg-amber-100"
                    isLoading={isWaitlisting}
                    onClick={handleJoinWaitlist}
                  >
                    Join Waitlist for {selectedDate}
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                  {availableSlots.map((s) => (
                    <button type="button" key={s.id} onClick={() => setSelectedTime(s.start_time)} className={`py-2 text-xs font-semibold rounded-xl border ${selectedTime === s.start_time ? 'bg-sky-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-50'}`}>
                      {s.start_time}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
        )}

        <Card className="space-y-4">
          <CardTitle>3. Reason for Visit (Optional)</CardTitle>
          <Input placeholder="e.g. Routine checkup, fever" value={reason} onChange={(e) => setReason(e.target.value)} />
        </Card>

        <Button type="submit" size="lg" className="w-full" disabled={!selectedDoctorId || !selectedDate || !selectedTime || isSubmitting} isLoading={isSubmitting} leftIcon={<CheckCircle2 className="w-5 h-5" />}>
          Confirm Appointment
        </Button>
      </form>
    </div>
  )
}
