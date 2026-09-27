import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { appointmentService } from '@/services/appointments'
import { reportService } from '@/services/reports'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import {
  Calendar,
  FileText,
  Sparkles,
  PhoneCall,
  ChevronRight,
  Stethoscope,
  Truck,
  Droplet,
  Building2,
  BellRing,
  ClipboardCheck,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const PatientDashboard: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ['patient-appointments'],
    queryFn: () => appointmentService.getMyAppointments(),
  })

  const { data: reports = [] } = useQuery({
    queryKey: ['patient-reports'],
    queryFn: () => reportService.getMyReports(),
  })

  const upcomingAppts = appointments.filter((a) => a.status === 'confirmed' || a.status === 'pending')

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-sky-700 to-teal-700 rounded-2xl p-6 text-white shadow-lg space-y-3">
        <div>
          <h1 className="text-2xl font-black tracking-tight">Welcome back, {user?.full_name}!</h1>
          <p className="text-xs text-sky-100 mt-0.5">ClinicCare Clinic Appointment, Patient & Emergency Management System</p>
        </div>
        <div className="pt-2 flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={() => navigate('/patient/appointments/book')}>
            Book Appointment
          </Button>
          <Button variant="outline" size="sm" className="text-white border-white/40 hover:bg-white/10" onClick={() => navigate('/patient/chat')}>
            <Sparkles className="w-4 h-4 mr-1" /> AI Assistant
          </Button>
          <Button variant="outline" size="sm" className="text-white border-white/40 hover:bg-white/10" onClick={() => navigate('/patient/ambulance')}>
            <Truck className="w-4 h-4 mr-1 text-rose-300" /> Ambulance
          </Button>
          <Button variant="outline" size="sm" className="text-white border-white/40 hover:bg-white/10" onClick={() => navigate('/patient/blood')}>
            <Droplet className="w-4 h-4 mr-1 text-pink-300" /> Blood Search
          </Button>
        </div>
      </div>


      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card hover onClick={() => navigate('/patient/appointments')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <Calendar className="w-6 h-6 text-sky-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Appointments</p>
            <p className="text-[11px] text-slate-500">{upcomingAppts.length} active</p>
          </div>
        </Card>
        <Card hover onClick={() => navigate('/patient/ambulance')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <Truck className="w-6 h-6 text-rose-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Ambulance</p>
            <p className="text-[11px] text-rose-600 font-semibold">Emergency</p>
          </div>
        </Card>
        <Card hover onClick={() => navigate('/patient/blood')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <Droplet className="w-6 h-6 text-pink-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Blood Search</p>
            <p className="text-[11px] text-slate-500">Live stock</p>
          </div>
        </Card>
        <Card hover onClick={() => navigate('/patient/facilities')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <Building2 className="w-6 h-6 text-teal-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Facilities</p>
            <p className="text-[11px] text-slate-500">Directory</p>
          </div>
        </Card>
        <Card hover onClick={() => navigate('/patient/visits')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <ClipboardCheck className="w-6 h-6 text-indigo-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Visit History</p>
            <p className="text-[11px] text-slate-500">Timeline</p>
          </div>
        </Card>
        <Card hover onClick={() => navigate('/patient/reminders')} className="cursor-pointer">
          <div className="p-3 text-center space-y-1">
            <BellRing className="w-6 h-6 text-amber-600 mx-auto" />
            <p className="text-xs font-bold text-slate-900">Reminders</p>
            <p className="text-[11px] text-slate-500">Follow-up</p>
          </div>
        </Card>
      </div>


      <Card>
        <CardHeader>
          <div>
            <CardTitle>Upcoming Consultations</CardTitle>
            <CardDescription>Your confirmed appointments</CardDescription>
          </div>
          <Link to="/patient/appointments" className="text-xs text-sky-600 font-bold flex items-center">View All <ChevronRight className="w-4 h-4" /></Link>
        </CardHeader>
        {isLoading ? (
          <div className="py-6 text-center text-xs text-slate-500">Loading...</div>
        ) : upcomingAppts.length === 0 ? (
          <div className="py-8 text-center space-y-2">
            <p className="text-sm font-semibold text-slate-700">No upcoming appointments</p>
            <Button size="sm" onClick={() => navigate('/patient/appointments/book')}>Book Now</Button>
          </div>
        ) : (
          <div className="space-y-3">
            {upcomingAppts.slice(0, 3).map((a) => (
              <div key={a.id} className="flex justify-between items-center p-3 rounded-xl border bg-slate-50">
                <div className="flex items-center gap-3">
                  <Stethoscope className="w-5 h-5 text-sky-600" />
                  <div>
                    <h4 className="text-sm font-bold">{a.doctor_name}</h4>
                    <p className="text-xs text-slate-500">{formatDate(a.appointment_date)} at {a.appointment_time}</p>
                  </div>
                </div>
                <Badge variant="success">{a.status}</Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
