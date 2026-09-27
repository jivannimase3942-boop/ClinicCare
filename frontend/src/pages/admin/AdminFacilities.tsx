import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { facilitiesApi } from '@/services/facilities'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { Building2, Plus, MapPin, Clock } from 'lucide-react'

export const AdminFacilities: React.FC = () => {
  const { showToast } = useToast()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [services, setServices] = useState('')
  const [address, setAddress] = useState('')
  const [phone, setPhone] = useState('')

  const { data: facilitiesData } = useQuery({
    queryKey: ['admin-facilities'],
    queryFn: () => facilitiesApi.getFacilities(),
  })

  const createMutation = useMutation({
    mutationFn: facilitiesApi.createFacility,
    onSuccess: () => {
      showToast('success', 'Facility registered successfully!')
      queryClient.invalidateQueries({ queryKey: ['admin-facilities'] })
      setShowModal(false)
      setName('')
      setServices('')
      setAddress('')
      setPhone('')
    },
  })

  const facilities = facilitiesData?.data || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Healthcare Facilities & Campuses</h2>
          <p className="text-sm text-slate-400 mt-1">Directory of hospital campuses and partner clinics.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs"
        >
          <Plus className="w-4 h-4" /> Register Facility
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {facilities.map((fac) => (
          <div key={fac.id} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="text-base font-bold text-white">{fac.name}</h4>
                <span className="text-xs text-sky-400 font-semibold">{fac.facility_type}</span>
              </div>
              {fac.is_emergency_ready && <Badge variant="danger">24/7 Trauma</Badge>}
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <p className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5" /> {fac.address}, {fac.city}</p>
              <p className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> {fac.operating_hours}</p>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
              <span className="font-bold text-slate-400 block mb-0.5">Services:</span>
              <span className="text-slate-300">{fac.services}</span>
            </div>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Tel: {fac.phone}</span>
              <span className="text-rose-400 font-bold">Hotline: {fac.emergency_hotline}</span>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4">
            <h3 className="text-lg font-bold text-white">Register Healthcare Facility</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                createMutation.mutate({ name, services, address, city: 'Metropolis', phone, emergency_hotline: '911' })
              }}
              className="space-y-3 text-xs"
            >
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Facility Name" className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-white" required />
              <input value={services} onChange={(e) => setServices(e.target.value)} placeholder="Services" className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-white" required />
              <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Address" className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-white" required />
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone" className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-white" required />
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 bg-slate-800 text-slate-300 rounded font-bold">Cancel</button>
                <button type="submit" className="flex-1 py-2 bg-sky-600 text-white rounded font-bold">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
