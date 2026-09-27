import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { doctorPortalService } from '@/services/doctor_portal'
import { Card, CardTitle, CardHeader, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Calendar, User, Clock, Stethoscope, CheckCircle } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const DoctorDashboard: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['doctor-appointments'],
    queryFn: () => doctorPortalService.getAppointments(),
  })

  const today = new Date().toISOString().split('T')[0]
  const todayAppts = appointments.filter((a) => a.appointment_date === today)
  const confirmed = appointments.filter((a) => a.status === 'confirmed')

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-teal-700 to-sky-800 rounded-3xl p-6 text-white space-y-2">
        <h1 className="text-2xl font-black">Welcome, {user?.full_name}!</h1>
        <p className="text-xs text-teal-100">Physician Clinical Portal • Patient consultations & schedule</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <Calendar className="w-8 h-8 text-teal-600" />
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase">Today's Visits</p>
              <p className="text-2xl font-black text-slate-900">{todayAppts.length}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-sky-600" />
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase">Active Schedule</p>
              <p className="text-2xl font-black text-slate-900">{confirmed.length}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-emerald-600" />
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase">Total Patients</p>
              <p className="text-2xl font-black text-slate-900">{appointments.length}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Upcoming Consultations</CardTitle>
            <CardDescription>Scheduled OPD patient appointments</CardDescription>
          </div>
          <Button size="sm" onClick={() => navigate('/doctor/appointments')}>
            Manage All
          </Button>
        </CardHeader>

        {isLoading ? (
          <p className="text-xs text-slate-400 py-6 text-center">Loading appointments...</p>
        ) : appointments.length === 0 ? (
          <p className="text-xs text-slate-500 py-8 text-center">No scheduled appointments found.</p>
        ) : (
          <div className="space-y-3">
            {appointments.slice(0, 5).map((a) => (
              <div key={a.id} className="p-3 bg-slate-50 rounded-xl border flex justify-between items-center text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900">{a.patient_name}</h4>
                    <p className="text-slate-500">{formatDate(a.appointment_date)} at {a.appointment_time}</p>
                  </div>
                </div>
                <Badge variant={a.status === 'confirmed' ? 'success' : 'default'}>{a.status}</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
