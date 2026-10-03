import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldCheck,
  CalendarCheck,
  Stethoscope,
  Building2,
  Lock,
  ArrowRight,
  UserCheck,
  FileCheck2,
  HeartPulse,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/context/AuthContext'

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()

  const handlePrimaryCta = () => {
    if (isAuthenticated && user) {
      if (user.role === 'ADMIN') navigate('/admin/dashboard')
      else if (user.role === 'FRONT_DESK') navigate('/frontdesk/dashboard')
      else if (user.role === 'DOCTOR') navigate('/doctor/dashboard')
      else navigate('/patient/dashboard')
    } else {
      navigate('/login')
    }
  }

  const pillars = [
    {
      icon: UserCheck,
      title: 'Patient Care & Appointments',
      description: 'Streamlined online appointment booking, digital visit histories, diagnostic reports, and automated follow-up reminders.',
    },
    {
      icon: Stethoscope,
      title: 'Physician Clinical Portal',
      description: 'Role-isolated consultation schedules, verified patient clinical context, and efficient patient visit documentation.',
    },
    {
      icon: Building2,
      title: 'Hospital Operations & Triage',
      description: 'Centralized front-desk coordination, doctor availability tracking, ambulance logistics, and emergency response.',
    },
  ]

  const securityFeatures = [
    {
      title: 'End-to-End Encrypted Records',
      desc: 'All medical profiles and diagnostic findings are isolated with strict cryptographic access boundaries.',
    },
    {
      title: 'Strict Role-Based Isolation',
      desc: 'Rigorous backend authorization ensures patients, physicians, and staff access only authorized resources.',
    },
    {
      title: 'Verified Email Identity',
      desc: 'Global single-identity enforcement prevents account duplication and unauthorized privilege escalation.',
    },
    {
      title: 'Audit-Ready Architecture',
      desc: 'Comprehensive logging, operational monitoring, and HIPAA-aligned clinical security principles.',
    },
  ]

  return (
    <div className="space-y-20 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-sky-50/80 via-white to-slate-50 pt-16 pb-20 lg:pt-24 lg:pb-28 border-b border-slate-200/80">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-100 text-sky-800 text-xs font-semibold tracking-wide">
            <ShieldCheck className="w-4 h-4 text-sky-600" />
            Verified Healthcare Management Platform
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15]">
            Unified Clinical Care & Hospital Orchestration
          </h1>

          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto font-normal">
            ClinicCare delivers a secure, dependable healthcare operations platform connecting patients,
            physicians, and administrative teams with conflict-free scheduling and role-isolated data management.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3.5 pt-4">
            <Button
              size="lg"
              variant="primary"
              onClick={handlePrimaryCta}
              className="px-6 py-3 font-semibold shadow-md shadow-sky-600/15"
            >
              {isAuthenticated ? 'Open Role Dashboard' : 'Sign In to Portal'}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/onboard-clinic')}
              className="px-6 py-3 font-semibold bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100"
            >
              Onboard Your Clinic
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/register')}
              rightIcon={<ArrowRight className="w-4 h-4" />}
              className="px-6 py-3 font-semibold bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              Get Started
            </Button>
          </div>

          <div className="pt-4 flex items-center justify-center gap-6 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-emerald-600" /> Encrypted Session
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-600" /> Multi-Role RBAC
            </span>
            <span className="flex items-center gap-1.5">
              <HeartPulse className="w-3.5 h-3.5 text-rose-600" /> Verified Accounts
            </span>
          </div>
        </div>
      </section>

      {/* How ClinicCare Works / Platform Pillars */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
          <span className="text-xs font-bold text-sky-700 uppercase tracking-widest">Platform Overview</span>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Designed for Modern Healthcare Operations
          </h2>
          <p className="text-sm text-slate-500">
            Dedicated interfaces and workflow automation customized for every role in the healthcare facility.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pillars.map((pillar, idx) => {
            const Icon = pillar.icon
            return (
              <div
                key={idx}
                className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-700">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{pillar.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{pillar.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Security & Data Privacy Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-900 rounded-3xl p-8 sm:p-12 text-white border border-slate-800 shadow-xl">
          <div className="max-w-2xl mb-10 space-y-2">
            <span className="text-xs font-bold text-sky-400 uppercase tracking-widest">Trust & Compliance</span>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Enterprise-Grade Clinical Data Security
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Patient privacy is our foundational architectural commitment. Sensitive clinical data and consultation
              records are safeguarded through multi-layered authorization.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {securityFeatures.map((feat, i) => (
              <div key={i} className="p-5 rounded-2xl bg-slate-800/80 border border-slate-700/60 space-y-1.5">
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                  {feat.title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
