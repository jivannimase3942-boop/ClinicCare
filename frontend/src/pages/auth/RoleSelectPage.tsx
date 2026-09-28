import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Activity,
  User,
  Stethoscope,
  Building2,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react'

export const RoleSelectPage: React.FC = () => {
  const navigate = useNavigate()

  const roles = [
    {
      title: 'Patient Account',
      role: 'PATIENT',
      badge: 'Public Self-Registration',
      badgeColor: 'bg-sky-50 text-sky-700 border-sky-200',
      icon: User,
      iconColor: 'bg-sky-100 text-sky-700',
      description: 'Book appointments with specialists, view digital medical reports, track visit history, and access health services.',
      benefits: [
        'Instant email OTP verification',
        'Direct consultation booking',
        'Secure medical reports & records',
      ],
      ctaText: 'Register as Patient',
      ctaLink: '/register/patient',
    },
    {
      title: 'Physician / Doctor Portal',
      role: 'DOCTOR',
      badge: 'Verification Required',
      badgeColor: 'bg-teal-50 text-teal-700 border-teal-200',
      icon: Stethoscope,
      iconColor: 'bg-teal-100 text-teal-700',
      description: 'Medical practitioners can request access to manage consultation schedules, review assigned patient charts, and record visits.',
      benefits: [
        'Verified physician access request',
        'Consultation schedule management',
        'Clinical patient visit records',
      ],
      ctaText: 'Request Doctor Access',
      ctaLink: '/register/doctor',
    },
    {
      title: 'Front Desk Operations',
      role: 'FRONT_DESK',
      badge: 'Admin Approval Required',
      badgeColor: 'bg-amber-50 text-amber-700 border-amber-200',
      icon: Building2,
      iconColor: 'bg-amber-100 text-amber-700',
      description: 'Hospital reception and operational staff can request onboarding for check-in desk, doctor availability, and ambulance coordination.',
      benefits: [
        'Staff identity verification',
        'Reception & appointment check-in',
        'Emergency & ambulance coordination',
      ],
      ctaText: 'Request Front Desk Access',
      ctaLink: '/register/frontdesk',
    },
  ]

  return (
    <div className="min-h-[calc(100vh-10rem)] py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-1">
          <Activity className="w-7 h-7 stroke-[2.5]" />
        </div>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Select Account Type</h1>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Choose your role in ClinicCare to proceed with secure onboarding or credential request
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {roles.map((r, i) => {
          const Icon = r.icon
          return (
            <div
              key={i}
              className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm hover:shadow-md hover:border-sky-300 transition flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${r.iconColor}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${r.badgeColor}`}>
                    {r.badge}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-slate-900">{r.title}</h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{r.description}</p>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  {r.benefits.map((b, bi) => (
                    <div key={bi} className="flex items-center gap-2 text-xs text-slate-600 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span>{b}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-6">
                <button
                  type="button"
                  onClick={() => navigate(r.ctaLink)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-sky-600 text-white text-xs font-semibold shadow-xs transition"
                >
                  <span>{r.ctaText}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <div className="text-center text-xs text-slate-500 pt-2">
        Already have a verified ClinicCare account?{' '}
        <Link to="/login" className="font-bold text-sky-600 hover:text-sky-700 underline decoration-sky-300 underline-offset-4">
          Sign In here
        </Link>
      </div>

      <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
        <ShieldCheck className="w-4 h-4 text-emerald-500" />
        <span>One verified email per identity • Privilege escalation strictly governed by administrator approval</span>
      </div>
    </div>
  )
}
