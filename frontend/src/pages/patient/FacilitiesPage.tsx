import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { facilitiesApi } from '@/services/facilities'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Building2, Search, MapPin, PhoneCall, Clock, Siren, Star, ShieldCheck } from 'lucide-react'

const TYPES = ['All', 'Hospital', 'Clinic', 'Diagnostic', 'Trauma']

export const FacilitiesPage: React.FC = () => {
  const [search, setSearch] = useState('')
  const [selectedType, setSelectedType] = useState('All')

  const { data, isLoading } = useQuery({
    queryKey: ['facilities', search, selectedType],
    queryFn: () =>
      facilitiesApi.getFacilities({
        search: search || undefined,
        facility_type: selectedType === 'All' ? undefined : selectedType,
      }),
  })

  const facilities = data?.data || []

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-gradient-to-r from-sky-700 to-teal-700 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 border border-white/20">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-black tracking-tight">ClinicCare Healthcare Facilities Directory</h2>
            <p className="text-xs text-sky-100 mt-0.5">
              Verified hospital campuses, outpatient clinics, diagnostics, and 24/7 trauma emergency hubs.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            {TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition shadow-sm ${
                  selectedType === t
                    ? 'bg-sky-600 text-white shadow-sky-200'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {t === 'All' ? 'All Facilities' : t}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-72">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by facility name or services..."
              className="pl-9 h-9 text-xs"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </div>
        </CardContent>
      </Card>

      {/* Facilities Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {facilities.map((fac) => (
          <Card key={fac.id} className="border-slate-200 hover:shadow-md transition">
            <CardContent className="p-5 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-base font-bold text-slate-900">{fac.name}</h4>
                    <span className="text-xs font-semibold text-sky-600">{fac.facility_type}</span>
                  </div>
                  {fac.is_emergency_ready && (
                    <Badge variant="danger" className="shrink-0 flex items-center gap-1 font-bold">
                      <Siren className="w-3 h-3" /> 24/7 Trauma Ready
                    </Badge>
                  )}
                </div>

                <div className="space-y-1.5 text-xs text-slate-600">
                  <p className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{fac.address}, {fac.city}</span>
                  </p>
                  <p className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{fac.operating_hours}</span>
                  </p>
                </div>

                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                    Specialized Services Offered:
                  </p>
                  <p className="text-xs text-slate-700 font-medium leading-relaxed">{fac.services}</p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-slate-700">{fac.phone}</span>
                <a
                  href={`tel:${fac.emergency_hotline}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100 font-bold text-xs transition"
                >
                  <PhoneCall className="w-3.5 h-3.5" /> Call Facility
                </a>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
