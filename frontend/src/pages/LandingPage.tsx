import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  CalendarCheck,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  HeartPulse,
  Activity,
  ArrowRight,
  Clock,
  PhoneCall,
  FileCheck,
  Award,
  Users,
  Truck,
  Droplet,
  Building2,
  BellRing,
  ClipboardCheck,
  Siren,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()

  const modules = [
    {
      icon: CalendarCheck,
      title: 'Appointment Booking',
      desc: 'Conflict-free appointment booking, specialist doctors, live time slots, rescheduling, and cancellation.',
      link: '/patient/appointments/book',
      color: 'bg-sky-50 text-sky-600 border-sky-100',
    },
    {
      icon: Sparkles,
      title: 'AI Health Assistant',
      desc: 'Smart administrative guidance, general medication lookup (e.g. cetirizine), and strict clinical safety guardrails.',
      link: '/patient/chat',
      color: 'bg-teal-50 text-teal-600 border-teal-100',
    },
    {
      icon: Truck,
      title: 'Ambulance Coordination',
      desc: 'Emergency ambulance request dispatch, live fleet status (BLS/ALS), and simulated ETA tracking.',
      link: '/patient/ambulance',
      color: 'bg-rose-50 text-rose-600 border-rose-100',
    },
    {
      icon: Droplet,
      title: 'Blood Group Search',
      desc: 'Instant search across 8 blood groups (A+, O+, B-, etc.), units in reserve, and 24/7 blood bank directory.',
      link: '/patient/blood',
      color: 'bg-pink-50 text-pink-600 border-pink-100',
    },
    {
      icon: Building2,
      title: 'Healthcare Facilities',
      desc: 'Directory of main hospital campuses, family clinics, trauma centers, and diagnostic pathology labs.',
      link: '/patient/facilities',
      color: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    },
    {
      icon: ClipboardCheck,
      title: 'Patient History & Visits',
      desc: 'Comprehensive patient profile, past consultation records, vital stats, and follow-up guidance.',
      link: '/patient/visits',
      color: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    },
    {
      icon: FileCheck,
      title: 'Diagnostic Reports',
      desc: 'Track pathology, imaging, and cardiology test reports digitally with instant ready notifications.',
      link: '/patient/reports',
      color: 'bg-amber-50 text-amber-600 border-amber-100',
    },
    {
      icon: BellRing,
      title: 'Follow-Up Reminders',
      desc: 'Scheduled appointment and follow-up alerts with simulated WhatsApp and SMS dispatches.',
      link: '/patient/reminders',
      color: 'bg-purple-50 text-purple-600 border-purple-100',
    },
  ]


  const stats = [
    { value: '100%', label: 'Deterministic Data Fallback' },
    { value: '8', label: 'Core Medical Modules' },
    { value: '< 5 Min', label: 'Ambulance Triage Response' },
    { value: '24/7', label: 'Emergency Ready Hub' },
  ]

  return (
    <div className="space-y-16 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-sky-50/70 via-white to-slate-50 pt-14 pb-16 lg:pt-20 lg:pb-24 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-100 text-sky-800 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              ClinicCare AI • FIT-FEST 2026 Edition
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15]">
              Clinic Appointment, Patient & Emergency Management
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
              Unified, demo-ready healthcare platform engineered for small clinics and multispeciality hospitals — featuring conflict-free scheduling, patient visit history, ambulance coordination, blood inventory, and safe AI assistance.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                size="lg"
                variant="primary"
                leftIcon={<CalendarCheck className="w-5 h-5" />}
                onClick={() => navigate('/patient/appointments/book')}
              >
                Book Appointment
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="bg-white hover:bg-rose-50 text-rose-600 border-rose-200 font-bold"
                leftIcon={<Truck className="w-5 h-5 text-rose-600" />}
                onClick={() => navigate('/patient/ambulance')}
              >
                Ambulance Dispatch
              </Button>
              <Button
                size="lg"
                variant="outline"
                leftIcon={<Sparkles className="w-5 h-5 text-teal-600" />}
                onClick={() => navigate('/patient/chat')}
              >
                AI Health Assistant
              </Button>
            </div>

            {/* Safety Disclaimer Banner */}
            <div className="mt-6 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center justify-center gap-2 max-w-2xl mx-auto">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>
                <strong>Medical Safety Notice:</strong> AI Assistant provides administrative & scheduling coordination. For medical emergencies dial 911 / 108.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((st, idx) => (
            <div key={idx} className="bg-white p-5 rounded-2xl border border-slate-200 text-center shadow-sm">
              <div className="text-2xl lg:text-3xl font-black text-sky-600 mb-0.5">{st.value}</div>
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{st.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 8 Core Functional Modules Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
          <Badge variant="primary" className="text-xs uppercase font-bold">Integrated Capabilities</Badge>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">8 Core Healthcare Modules</h2>
          <p className="text-slate-600 text-xs sm:text-sm">Click any module below to explore the interactive workflows.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {modules.map((m, i) => {
            const Icon = m.icon
            return (
              <div
                key={i}
                onClick={() => navigate(m.link)}
                className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md hover:border-sky-300 transition cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 border ${m.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-1.5">{m.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{m.desc}</p>
                </div>
                <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-sky-600">
                  <span>Explore Module</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

