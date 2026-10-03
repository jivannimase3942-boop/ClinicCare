import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Building2,
  Stethoscope,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Clock,
  MapPin,
  Mail,
  Phone,
  Sparkles,
  KeyRound,
  UserCheck,
  Hospital,
  DollarSign,
  AlertCircle,
  Copy,
  ExternalLink,
} from 'lucide-react'
import { clinicService, ClinicOnboardPayload, ClinicOnboardResult } from '@/services/clinic'
import { useToast } from '@/context/ToastContext'

const PRESET_DEPARTMENTS = [
  'General Medicine',
  'Pediatrics',
  'Cardiology',
  'Orthopedics',
  'Gynecology & Obstetrics',
  'Dermatology',
  'ENT (Otolaryngology)',
  'Ophthalmology',
  'Dental Care',
  'Ayurvedic & Integrative',
]

const PRESET_SERVICES = [
  'OPD Consultation',
  'Emergency Care & Triage',
  'Routine Health Checkup',
  'Diagnostic Sample Collection',
  'Vaccination & Immunization',
  'Minor Surgical Procedures',
  'Teleconsultation Support',
]

export const ClinicOnboardingPage: React.FC = () => {
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [onboardResult, setOnboardResult] = useState<ClinicOnboardResult | null>(null)

  // Form State
  const [formData, setFormData] = useState<ClinicOnboardPayload>({
    name: '',
    slug: '',
    phone: '',
    email: '',
    address: '',
    city: 'Bengaluru',
    state: 'Karnataka',
    pincode: '560001',
    country: 'India',
    operating_hours: '08:00 AM - 08:00 PM (Monday - Saturday)',
    consultation_fee_default: 500,
    departments: ['General Medicine', 'Pediatrics', 'Cardiology'],
    services: ['OPD Consultation', 'Routine Health Checkup', 'Diagnostic Sample Collection'],
    admin_name: '',
    admin_email: '',
    admin_password: '',
    admin_phone: '',
    doctor_name: '',
    doctor_email: '',
    doctor_specialization: 'General Physician',
    doctor_qualification: 'MBBS, MD',
    doctor_fee: 500,
  })

  // Auto-generate slug when name changes
  const handleNameChange = (name: string) => {
    const slug = name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
    setFormData((prev) => ({
      ...prev,
      name,
      slug: !prev.slug || (prev.name && prev.slug.startsWith(prev.name.toLowerCase().substring(0, 3))) ? slug : prev.slug,
    }))
  }

  const toggleDepartment = (dept: string) => {
    setFormData((prev) => {
      const current = prev.departments || []
      const exists = current.includes(dept)
      return {
        ...prev,
        departments: exists ? current.filter((d) => d !== dept) : [...current, dept],
      }
    })
  }

  const toggleService = (srv: string) => {
    setFormData((prev) => {
      const current = prev.services || []
      const exists = current.includes(srv)
      return {
        ...prev,
        services: exists ? current.filter((s) => s !== srv) : [...current, srv],
      }
    })
  }

  const validateStep1 = () => {
    if (!formData.name.trim()) return 'Clinic Name is required'
    if (!formData.phone?.trim()) return 'Clinic Contact Phone is required'
    if (!formData.address?.trim()) return 'Clinic Address is required'
    return null
  }

  const validateStep2 = () => {
    if (!formData.departments || formData.departments.length === 0) {
      return 'Please select at least one clinical department'
    }
    if ((formData.consultation_fee_default || 0) < 0) {
      return 'Consultation fee cannot be negative'
    }
    return null
  }

  const validateStep3 = () => {
    if (!formData.admin_name.trim()) return 'Administrator full name is required'
    if (!formData.admin_email.trim() || !formData.admin_email.includes('@')) {
      return 'Valid administrator email address is required'
    }
    if (!formData.admin_password || formData.admin_password.length < 6) {
      return 'Password must be at least 6 characters long'
    }
    return null
  }

  const handleNext = () => {
    setErrorMessage(null)
    if (step === 1) {
      const err = validateStep1()
      if (err) {
        setErrorMessage(err)
        return
      }
      setStep(2)
    } else if (step === 2) {
      const err = validateStep2()
      if (err) {
        setErrorMessage(err)
        return
      }
      setStep(3)
    } else if (step === 3) {
      const err = validateStep3()
      if (err) {
        setErrorMessage(err)
        return
      }
      handleSubmit()
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      const result = await clinicService.onboardClinic(formData)
      setOnboardResult(result)
      setStep(4)
      showToast(`Clinic "${result.clinic.name}" successfully onboarded!`, 'success')
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || 'Clinic onboarding failed. Please try again.'
      setErrorMessage(msg)
      showToast(msg, 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-0.5 shadow-lg shadow-emerald-900/30 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Hospital className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                ClinicCare
              </span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                SaaS Onboarding
              </span>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Existing Clinic? Log in
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 w-full flex-1">
        {/* Wizard Progress Stepper */}
        {step < 4 && (
          <div className="mb-10">
            <div className="flex items-center justify-between max-w-2xl mx-auto">
              {[
                { s: 1, label: 'Clinic Profile', icon: Building2 },
                { s: 2, label: 'Departments & Fees', icon: Stethoscope },
                { s: 3, label: 'Admin Setup', icon: ShieldCheck },
              ].map(({ s, label, icon: Icon }) => (
                <div key={s} className="flex flex-col items-center relative z-10">
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 font-bold ${
                      step === s
                        ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30 ring-4 ring-emerald-500/20 scale-105'
                        : step > s
                        ? 'bg-emerald-600/30 text-emerald-400 border border-emerald-500/40'
                        : 'bg-slate-900 text-slate-500 border border-slate-800'
                    }`}
                  >
                    {step > s ? <CheckCircle2 className="w-6 h-6 text-emerald-400" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span
                    className={`text-xs mt-2 font-medium ${
                      step === s ? 'text-emerald-400 font-semibold' : step > s ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {label}
                  </span>
                </div>
              ))}
            </div>
            <div className="relative mt-[-28px] max-w-md mx-auto h-0.5 bg-slate-800 -z-0">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                style={{ width: `${((step - 1) / 2) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/50 border border-red-800/80 text-red-200 text-sm flex items-center gap-3 animate-shake">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Step 1: Clinic Information */}
        {step === 1 && (
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <Building2 className="w-7 h-7 text-emerald-400" /> Clinic Organization Profile
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Establish your healthcare organization on the ClinicCare multi-tenant cloud platform.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Clinic / Hospital Name *
                </label>
                <input
                  id="clinic-name-input"
                  type="text"
                  placeholder="e.g. Apollo CityCare Clinic, Koramangala"
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Portal Slug / URL Identifier
                </label>
                <div className="flex items-center rounded-xl bg-slate-950 border border-slate-800 px-3 text-slate-400 text-sm">
                  <span className="text-slate-500 text-xs">/clinic/</span>
                  <input
                    id="clinic-slug-input"
                    type="text"
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    placeholder="apollo-citycare"
                    className="w-full bg-transparent py-3 text-emerald-400 focus:outline-none text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Primary Contact Phone *
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="clinic-phone-input"
                    type="tel"
                    placeholder="+91 80 2345 6789"
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Official Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="clinic-email-input"
                    type="email"
                    placeholder="contact@citycare.in"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Operating Hours
                </label>
                <div className="relative">
                  <Clock className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="clinic-hours-input"
                    type="text"
                    placeholder="08:00 AM - 08:00 PM (Mon-Sat)"
                    value={formData.operating_hours || ''}
                    onChange={(e) => setFormData({ ...formData, operating_hours: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Clinic Street Address *
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="clinic-address-input"
                    type="text"
                    placeholder="100 80ft Road, 4th Block, Koramangala"
                    value={formData.address || ''}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  City
                </label>
                <input
                  id="clinic-city-input"
                  type="text"
                  value={formData.city || 'Bengaluru'}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    State
                  </label>
                  <input
                    id="clinic-state-input"
                    type="text"
                    value={formData.state || 'Karnataka'}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                    PIN Code
                  </label>
                  <input
                    id="clinic-pin-input"
                    type="text"
                    placeholder="560034"
                    value={formData.pincode || ''}
                    onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                id="onboard-step1-next"
                type="button"
                onClick={handleNext}
                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all hover:translate-x-0.5"
              >
                Continue to Departments <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Clinical Services & Fees */}
        {step === 2 && (
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <Stethoscope className="w-7 h-7 text-emerald-400" /> Departments & Clinical Services
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Configure your active outpatient departments, consultation charges, and patient offerings.
              </p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
                  Select Active Departments (Tap to toggle)
                </label>
                <div className="flex flex-wrap gap-2">
                  {PRESET_DEPARTMENTS.map((dept) => {
                    const isSelected = formData.departments?.includes(dept)
                    return (
                      <button
                        key={dept}
                        type="button"
                        onClick={() => toggleDepartment(dept)}
                        className={`px-3.5 py-2 rounded-xl text-xs font-medium border transition-all ${
                          isSelected
                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-sm shadow-emerald-500/10'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                      >
                        {isSelected && '✓ '}
                        {dept}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
                  Clinical Services Offered
                </label>
                <div className="flex flex-wrap gap-2">
                  {PRESET_SERVICES.map((srv) => {
                    const isSelected = formData.services?.includes(srv)
                    return (
                      <button
                        key={srv}
                        type="button"
                        onClick={() => toggleService(srv)}
                        className={`px-3.5 py-2 rounded-xl text-xs font-medium border transition-all ${
                          isSelected
                            ? 'bg-teal-500/20 border-teal-500 text-teal-300 shadow-sm shadow-teal-500/10'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                      >
                        {isSelected && '✓ '}
                        {srv}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800/80">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Default Consultation Fee (INR ₹)
                </label>
                <div className="max-w-xs relative">
                  <span className="absolute left-4 top-3.5 text-slate-400 font-bold text-sm">₹</span>
                  <input
                    id="clinic-fee-input"
                    type="number"
                    min="0"
                    step="50"
                    placeholder="500"
                    value={formData.consultation_fee_default || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, consultation_fee_default: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-slate-100 font-semibold focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Individual practitioners can adjust custom consultation rates if needed.
                </p>
              </div>
            </div>

            <div className="mt-8 flex justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl flex items-center gap-2 transition-all"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                id="onboard-step2-next"
                type="button"
                onClick={handleNext}
                className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all hover:translate-x-0.5"
              >
                Configure Administrator <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Admin & Doctor Credentials */}
        {step === 3 && (
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <ShieldCheck className="w-7 h-7 text-emerald-400" /> Primary Administrator Credentials
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                This account will hold master administrative governance over your clinic's staff, doctors, appointments, and billing.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-8">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Admin Full Name *
                </label>
                <div className="relative">
                  <UserCheck className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="admin-name-input"
                    type="text"
                    placeholder="Dr. Rajesh Patel"
                    value={formData.admin_name}
                    onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Admin Email (Login ID) *
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="admin-email-input"
                    type="email"
                    placeholder="admin@myclinic.in"
                    value={formData.admin_email}
                    onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Secure Password *
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="admin-password-input"
                    type="password"
                    placeholder="••••••••••••"
                    value={formData.admin_password}
                    onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Admin Phone
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    id="admin-phone-input"
                    type="tel"
                    placeholder="+91 98765 43210"
                    value={formData.admin_phone || ''}
                    onChange={(e) => setFormData({ ...formData, admin_phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 transition-all"
                  />
                </div>
              </div>
            </div>

            {/* Optional Lead Doctor */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 mb-6">
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-1 flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-teal-400" /> Initial Medical Practitioner (Optional)
              </h2>
              <p className="text-xs text-slate-400 mb-4">
                You can immediately provision your lead specialist or add doctors later from the Admin Console.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Doctor Name</label>
                  <input
                    id="doctor-name-input"
                    type="text"
                    placeholder="Dr. Sneha Roy"
                    value={formData.doctor_name || ''}
                    onChange={(e) => setFormData({ ...formData, doctor_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Doctor Email</label>
                  <input
                    id="doctor-email-input"
                    type="email"
                    placeholder="doctor@myclinic.in"
                    value={formData.doctor_email || ''}
                    onChange={(e) => setFormData({ ...formData, doctor_email: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Specialization</label>
                  <input
                    id="doctor-spec-input"
                    type="text"
                    placeholder="General Physician / Pediatrician"
                    value={formData.doctor_specialization || ''}
                    onChange={(e) => setFormData({ ...formData, doctor_specialization: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Consultation Fee (₹)</label>
                  <input
                    id="doctor-fee-input"
                    type="number"
                    placeholder="500"
                    value={formData.doctor_fee || ''}
                    onChange={(e) => setFormData({ ...formData, doctor_fee: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-between">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl flex items-center gap-2 transition-all"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                id="onboard-submit-btn"
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold rounded-xl flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    Provisioning Clinic...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" /> Complete Clinic Onboarding
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Success & Activation Confirmation */}
        {step === 4 && onboardResult && (
          <div className="bg-slate-900/80 border border-emerald-500/40 rounded-3xl p-8 sm:p-10 backdrop-blur-2xl shadow-2xl text-center">
            <div className="w-20 h-20 rounded-3xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-500/20">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 animate-bounce" />
            </div>

            <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
              Welcome to ClinicCare!
            </h1>
            <p className="text-emerald-400 font-semibold text-lg mb-4">
              {onboardResult.clinic.name} is now live
            </p>
            <p className="text-slate-400 max-w-lg mx-auto text-sm mb-8">
              Your clinic tenant has been isolated, initialized with RBAC security controls, and audited into the SaaS foundation.
            </p>

            <div className="max-w-md mx-auto bg-slate-950/80 rounded-2xl border border-slate-800 p-5 text-left mb-8 space-y-3">
              <div className="flex justify-between items-center text-xs border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Clinic Slug</span>
                <span className="font-mono text-emerald-300 font-medium">{onboardResult.clinic.slug}</span>
              </div>
              <div className="flex justify-between items-center text-xs border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Admin Email</span>
                <span className="font-medium text-slate-200">{onboardResult.admin_user.email}</span>
              </div>
              <div className="flex justify-between items-center text-xs border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Role</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  {onboardResult.admin_user.role}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs pt-1">
                <span className="text-slate-400">Public Profile</span>
                <span className="font-mono text-xs text-teal-400 flex items-center gap-1">
                  /clinic/{onboardResult.clinic.slug}
                </span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                id="login-clinic-btn"
                to="/login"
                className="w-full sm:w-auto px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2"
              >
                Log In to Admin Portal <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/"
                className="w-full sm:w-auto px-6 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-xl transition-all"
              >
                Return to Home
              </Link>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        © 2026 ClinicCare SaaS Platform. Powered by India Healthcare Operations Engine.
      </footer>
    </div>
  )
}
