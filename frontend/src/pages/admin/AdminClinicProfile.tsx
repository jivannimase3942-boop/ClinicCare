import React, { useState, useEffect } from 'react'
import {
  Hospital,
  Building2,
  Clock,
  MapPin,
  Phone,
  Mail,
  DollarSign,
  ExternalLink,
  Save,
  CheckCircle2,
  Shield,
} from 'lucide-react'
import { clinicService } from '@/services/clinic'
import { Clinic } from '@/types'
import { useToast } from '@/context/ToastContext'

export const AdminClinicProfile: React.FC = () => {
  const { showToast } = useToast()
  const [clinic, setClinic] = useState<Clinic | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  // Edit form state
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [address, setAddress] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [pincode, setPincode] = useState('')
  const [operatingHours, setOperatingHours] = useState('')
  const [consultationFee, setConsultationFee] = useState<number>(500)

  const fetchClinic = async () => {
    try {
      setIsLoading(true)
      const data = await clinicService.getCurrentClinic()
      setClinic(data)
      setName(data.name || '')
      setPhone(data.phone || '')
      setEmail(data.email || '')
      setAddress(data.address || '')
      setCity(data.city || '')
      setState(data.state || '')
      setPincode(data.pincode || '')
      setOperatingHours(data.operating_hours || '')
      setConsultationFee(data.consultation_fee_default || 500)
    } catch (err: any) {
      showToast('Failed to load clinic profile', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchClinic()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      const updated = await clinicService.updateCurrentClinic({
        name,
        phone,
        email,
        address,
        city,
        state,
        pincode,
        operating_hours: operatingHours,
        consultation_fee_default: consultationFee,
      })
      setClinic(updated)
      showToast('Clinic profile updated successfully', 'success')
    } catch (err: any) {
      showToast(err.message || 'Failed to update clinic profile', 'error')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs">Loading clinic settings...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Hospital className="w-7 h-7 text-emerald-400" /> Clinic Organization Profile & Settings
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage your facility's public information, operating schedule, and consultation standards.
          </p>
        </div>

        {clinic?.slug && (
          <a
            href={`/clinic/${clinic.slug}`}
            target="_blank"
            rel="noreferrer"
            className="self-start sm:self-auto px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors"
          >
            <span>Public Microsite</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSave} className="bg-slate-950/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Clinic Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Organization Slug (Identifier)
            </label>
            <input
              type="text"
              value={clinic?.slug || ''}
              disabled
              className="w-full bg-slate-900/40 border border-slate-800/60 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-400 cursor-not-allowed"
            />
            <span className="text-[11px] text-slate-500 mt-1 block">Used in your shareable booking URL.</span>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Default OPD Consultation Fee (₹)
            </label>
            <input
              type="number"
              min="0"
              step="50"
              value={consultationFee}
              onChange={(e) => setConsultationFee(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-semibold text-emerald-400 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Contact Phone
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Contact Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Operating Hours
            </label>
            <input
              type="text"
              value={operatingHours}
              onChange={(e) => setOperatingHours(e.target.value)}
              placeholder="e.g. 08:00 AM - 08:00 PM (Monday - Saturday)"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Street Address
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              City
            </label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                State
              </label>
              <input
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                PIN Code
              </label>
              <input
                type="text"
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                Saving Changes...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" /> Save Clinic Settings
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
