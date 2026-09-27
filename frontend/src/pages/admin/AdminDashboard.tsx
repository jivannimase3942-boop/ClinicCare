import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Stethoscope,
  Calendar,
  Truck,
  Droplet,
  Siren,
  Star,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const COLORS = ['#0284c7', '#0d9488', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981']

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate()
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminService.getStats(),
  })

  if (isLoading || !stats) {
    return <div className="text-center py-20 text-slate-400 text-sm">Loading clinic metrics dashboard...</div>
  }

  const { metrics } = stats

  const summaryCards = [
    { label: 'Total Patients', value: metrics.total_patients, icon: Users, color: 'text-sky-400 bg-sky-950/50 border-sky-800/50', link: '/admin/patients' },
    { label: "Today's Appointments", value: metrics.today_appointments, icon: Calendar, color: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/50', link: '/admin/appointments' },
    { label: 'Upcoming Consultations', value: metrics.upcoming_appointments, icon: TrendingUp, color: 'text-blue-400 bg-blue-950/50 border-blue-800/50', link: '/admin/appointments' },
    { label: 'Completed Consultations', value: metrics.completed_appointments || 0, icon: CheckCircle2, color: 'text-teal-400 bg-teal-950/50 border-teal-800/50', link: '/admin/appointments' },
    { label: 'Active Ambulances', value: metrics.active_ambulances || 0, icon: Truck, color: 'text-amber-400 bg-amber-950/50 border-amber-800/50', link: '/admin/ambulances' },
    { label: 'Emergency Requests', value: metrics.emergency_requests || 0, icon: Siren, color: 'text-rose-400 bg-rose-950/50 border-rose-800/50', link: '/admin/emergency' },
    { label: 'Available Blood Units', value: metrics.available_blood_units || 0, icon: Droplet, color: 'text-pink-400 bg-pink-950/50 border-pink-800/50', link: '/admin/blood-bank' },
    { label: 'Patient Satisfaction', value: `${metrics.average_rating} / 5`, icon: Star, color: 'text-yellow-400 bg-yellow-950/50 border-yellow-800/50', link: '/admin/feedback' },
  ]


  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Hospital Administration & Analytics</h1>
        <p className="text-xs text-slate-400">Autonomous workflow monitoring, patient triage, and resource allocation</p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((c, i) => {
          const Icon = c.icon
          return (
            <div
              key={i}
              onClick={() => c.link && navigate(c.link)}
              className="bg-slate-800/80 p-4 rounded-2xl border border-slate-700 flex items-center gap-3.5 hover:border-slate-500 cursor-pointer transition"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${c.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase">{c.label}</p>
                <p className="text-xl font-black text-white mt-0.5">{c.value}</p>
              </div>
            </div>
          )
        })}
      </div>


      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Appointments 7-Day Trend */}
        <div className="bg-slate-800/90 p-5 rounded-2xl border border-slate-700 space-y-4">
          <h3 className="text-sm font-bold text-white">7-Day Appointment Bookings</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.appointments_by_day}>
                <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '12px' }} />
                <Bar dataKey="value" fill="#0284c7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-slate-800/90 p-5 rounded-2xl border border-slate-700 space-y-4">
          <h3 className="text-sm font-bold text-white">Appointment Status Distribution</h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={stats.appointment_status_distribution} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={80} label>
                  {stats.appointment_status_distribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
