import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useNavigate } from 'react-router-dom'
import {
  Users,
  Calendar,
  Truck,
  Siren,
  CheckCircle2,
  Clock,
  ArrowRight,
  Stethoscope,
  AlertTriangle,
  UserPlus,
  Activity,
  PhoneCall,
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

export const FrontDeskDashboard: React.FC = () => {
  const navigate = useNavigate()
  const { data: stats, isLoading } = useQuery({
    queryKey: ['frontdesk-stats'],
    queryFn: () => adminService.getStats(),
    refetchInterval: 30000,
  })

  if (isLoading || !stats) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm font-medium">Synchronizing reception desk operational metrics...</p>
      </div>
    )
  }

  const { metrics } = stats

  const operationalCards = [
    {
      label: "Today's Consultations",
      value: metrics.today_appointments,
      subtitle: `${metrics.upcoming_appointments || 0} pending arrival`,
      icon: Calendar,
      color: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/50',
      link: '/frontdesk/appointments',
    },
    {
      label: 'Registered Patients',
      value: metrics.total_patients,
      subtitle: 'Active clinical profiles',
      icon: Users,
      color: 'text-sky-400 bg-sky-950/50 border-sky-800/50',
      link: '/frontdesk/patients',
    },
    {
      label: 'Emergency Intake',
      value: metrics.emergency_requests || 0,
      subtitle: 'Critical triage queue',
      icon: Siren,
      color: 'text-rose-400 bg-rose-950/50 border-rose-800/50',
      link: '/frontdesk/emergency',
    },
    {
      label: 'Fleet / Ambulances',
      value: `${metrics.active_ambulances || 0} active`,
      subtitle: 'Ready for emergency transit',
      icon: Truck,
      color: 'text-amber-400 bg-amber-950/50 border-amber-800/50',
      link: '/frontdesk/ambulances',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Reception Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950/40 p-6 rounded-2xl border border-slate-700/80 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Reception Desk Operational
            </span>
            <span className="text-xs text-slate-400 font-mono">STATION-FD-01</span>
          </div>
          <h1 className="text-2xl font-black text-white">Patient Intake & Reception Control</h1>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Coordinate patient arrivals, emergency dispatches, on-duty physician schedules, and urgent escalations in real time.
          </p>
        </div>

        {/* Rapid Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => navigate('/frontdesk/patients')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 transition active:scale-95"
          >
            <UserPlus className="w-4 h-4" />
            Walk-in Patient
          </button>
          <button
            onClick={() => navigate('/frontdesk/appointments')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold border border-slate-600 transition active:scale-95"
          >
            <Calendar className="w-4 h-4" />
            Check-In Arrival
          </button>
          <button
            onClick={() => navigate('/frontdesk/emergency')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-950/40 transition active:scale-95"
          >
            <Siren className="w-4 h-4" />
            Emergency Dispatch
          </button>
        </div>
      </div>

      {/* Operational KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {operationalCards.map((card, idx) => {
          const Icon = card.icon
          return (
            <div
              key={idx}
              onClick={() => navigate(card.link)}
              className="bg-slate-800/90 hover:bg-slate-800 p-5 rounded-2xl border border-slate-700 hover:border-slate-600 transition shadow-sm cursor-pointer group flex flex-col justify-between"
            >
              <div className="flex items-start justify-between">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center border ${card.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 group-hover:translate-x-0.5 transition" />
              </div>
              <div className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{card.label}</p>
                <p className="text-2xl font-black text-white mt-1">{card.value}</p>
                <p className="text-xs text-slate-400 mt-1 font-medium">{card.subtitle}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Access Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointments Activity Trend */}
        <div className="lg:col-span-2 bg-slate-800/90 p-5 rounded-2xl border border-slate-700 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                7-Day Clinic Appointment Traffic
              </h3>
              <p className="text-xs text-slate-400">Incoming bookings and scheduled consultations</p>
            </div>
            <button
              onClick={() => navigate('/frontdesk/appointments')}
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
            >
              View Schedule <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.appointments_by_day}>
                <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    color: '#fff',
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Appointment Status Distribution */}
        <div className="bg-slate-800/90 p-5 rounded-2xl border border-slate-700 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-sky-400" />
                Appointment Flow Status
              </h3>
              <button
                onClick={() => navigate('/frontdesk/appointments')}
                className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1"
              >
                Directory <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">Breakdown of scheduled vs active visits</p>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.appointment_status_distribution || []}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                >
                  {(stats.appointment_status_distribution || []).map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    color: '#fff',
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-slate-700/60">
            {(stats.appointment_status_distribution || []).slice(0, 3).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium capitalize">{item.label}</span>
                <span className="font-bold text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Front Desk Protocols & Quick Triage Reference */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/80 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-white">Emergency Protocols</h4>
            <p className="text-xs text-slate-300 mt-0.5">
              Trauma or severe cardiac events must be dispatched immediately to the ER queue before paperwork. Dispatch ambulances via the Emergency module.
            </p>
          </div>
        </div>

        <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/80 flex items-start gap-3">
          <PhoneCall className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-white">Administrative Escalation</h4>
            <p className="text-xs text-slate-300 mt-0.5">
              For security incidents, billing adjustments, or doctor roster reassignment, register a ticket directly in the Escalations queue.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FrontDeskDashboard
