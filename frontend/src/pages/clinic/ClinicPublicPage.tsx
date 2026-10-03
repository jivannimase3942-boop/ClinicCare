import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Hospital,
  MapPin,
  Clock,
  Phone,
  Mail,
  Calendar,
  CheckCircle2,
  Stethoscope,
  Shield,
  ArrowRight,
  ExternalLink,
} from 'lucide-react'
import { clinicService, PublicClinicProfile } from '@/services/clinic'

export const ClinicPublicPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>()
  const [clinic, setClinic] = useState<PublicClinicProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    const fetchClinic = async () => {
      try {
        setIsLoading(true)
        const data = await clinicService.getPublicClinic(slug)
        setClinic(data)
      } catch (err: any) {
        setError('Clinic microsite not found or currently offline.')
      } finally {
        setIsLoading(false)
      }
    }
    fetchClinic()
  }, [slug])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading clinic profile...</p>
        </div>
      </div>
    )
  }

  if (error || !clinic) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-100 p-4">
        <div className="max-w-md text-center bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <Hospital className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h1 className="text-xl font-bold mb-2">Clinic Not Found</h1>
          <p className="text-sm text-slate-400 mb-6">{error || 'This clinic profile does not exist.'}</p>
          <Link
            to="/"
            className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-sm inline-block"
          >
            Go to ClinicCare Central
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-0.5 shadow-md flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Hospital className="w-4 h-4 text-emerald-400" />
              </div>
            </div>
            <span className="text-base font-bold tracking-tight text-white">ClinicCare</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-xs font-semibold px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              Staff Portal
            </Link>
            <Link
              to="/login"
              className="text-xs font-semibold px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors shadow-md shadow-emerald-500/20"
            >
              Patient Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Hero / Clinic Header */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-12 w-full flex-1">
        <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800/80 rounded-3xl p-8 sm:p-12 relative overflow-hidden shadow-2xl mb-8">
          <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-4">
                <Shield className="w-3.5 h-3.5" /> Verified Healthcare Organization
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
                {clinic.name}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-400">
                {clinic.city && (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-emerald-400 shrink-0" />
                    {clinic.address ? `${clinic.address}, ` : ''}{clinic.city}, {clinic.state}
                  </span>
                )}
                {clinic.operating_hours && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-teal-400 shrink-0" />
                    {clinic.operating_hours}
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-5 shrink-0 text-center sm:text-right">
              <span className="text-xs text-slate-400 uppercase tracking-wider block mb-1">Consultation Fee</span>
              <span className="text-2xl font-black text-emerald-400">₹{clinic.consultation_fee_default}</span>
              <span className="text-xs text-slate-500 block mt-0.5">Standard OPD</span>
              <Link
                to="/login"
                className="mt-4 px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/20 transition-all"
              >
                Book Appointment <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Departments */}
          <div className="md:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-emerald-400" /> Active Medical Departments
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {clinic.departments.map((dept, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 hover:border-emerald-500/40 transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 font-bold text-xs">
                    {dept.charAt(0)}
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-slate-200">{dept}</span>
                    <span className="block text-[11px] text-slate-500">Outpatient Consultation</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contact Details */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Phone className="w-5 h-5 text-teal-400" /> Contact & Helpdesk
            </h2>

            <div className="space-y-4 text-xs sm:text-sm">
              {clinic.phone && (
                <div>
                  <span className="text-slate-500 block text-xs uppercase mb-1">Phone Number</span>
                  <a href={`tel:${clinic.phone}`} className="font-semibold text-emerald-400 hover:underline">
                    {clinic.phone}
                  </a>
                </div>
              )}
              {clinic.email && (
                <div>
                  <span className="text-slate-500 block text-xs uppercase mb-1">Email Address</span>
                  <a href={`mailto:${clinic.email}`} className="font-semibold text-slate-200 hover:underline">
                    {clinic.email}
                  </a>
                </div>
              )}
              <div>
                <span className="text-slate-500 block text-xs uppercase mb-1">Facility Address</span>
                <p className="text-slate-300">
                  {clinic.address || 'Central OPD'}<br />
                  {clinic.city}, {clinic.state} {clinic.pincode ? `- ${clinic.pincode}` : ''}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/80">
              <Link
                to="/register"
                className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
              >
                Register as Patient
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        © 2026 {clinic.name}. Powered by ClinicCare Healthcare Cloud.
      </footer>
    </div>
  )
}
