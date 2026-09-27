import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { patientsApi, PatientRecord } from '@/services/patients'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Search, User, X, Eye, FileText, Calendar, Activity, PhoneCall, MapPin } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const AdminPatients: React.FC = () => {
  const [search, setSearch] = useState('')
  const [selectedPatient, setSelectedPatient] = useState<PatientRecord | null>(null)

  const { data: patientsData, isLoading } = useQuery({
    queryKey: ['admin-patients', search],
    queryFn: () => patientsApi.searchPatients({ search: search || undefined }),
  })

  const { data: visitsData } = useQuery({
    queryKey: ['admin-patient-visits', selectedPatient?.id],
    queryFn: () => (selectedPatient ? patientsApi.getPatientVisits(selectedPatient.id) : Promise.resolve({ success: true, data: [] })),
    enabled: !!selectedPatient,
  })

  const patients = patientsData?.data || []
  const visits = visitsData?.data || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Patient Directory & Clinical History</h1>
          <p className="text-xs text-slate-400 mt-1">
            Search patient records, view medical demographics, and review past visit history.
          </p>
        </div>
        <Badge variant="neutral" className="bg-slate-800 text-slate-300 w-fit">
          {patients.length} Registered Patients
        </Badge>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-2 max-w-lg">
        <div className="relative flex-1">
          <Input
            placeholder="Search by Name, Patient ID, Phone, Email, Blood Group..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
            className="bg-slate-900 text-white border-slate-800 placeholder:text-slate-500 text-xs"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading patient registry...</div>
      ) : patients.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">
          No patients found matching "{search}". Try searching with a different name or phone number.
        </div>
      ) : (
        <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Contact</th>
                <th className="p-4">Gender</th>
                <th className="p-4">Blood Group</th>
                <th className="p-4">Registered</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {patients.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/40 transition">
                  <td className="p-4 font-bold text-white flex items-center gap-2">
                    <User className="w-4 h-4 text-sky-400" />
                    <div>
                      <span>{p.full_name}</span>
                      <span className="text-[10px] text-slate-500 font-mono block">ID: {p.id.slice(0, 8)}</span>
                    </div>
                  </td>
                  <td className="p-4 text-slate-300">
                    <div>{p.email}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{p.phone || 'No phone'}</div>
                  </td>
                  <td className="p-4 capitalize">{p.gender || 'N/A'}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                      {p.blood_group || 'N/A'}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400">{formatDate(p.created_at)}</td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => setSelectedPatient(p)}
                      className="px-2.5 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs flex items-center gap-1 inline-flex"
                    >
                      <Eye className="w-3.5 h-3.5" /> View History
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Patient Details & Visit History Modal */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <User className="w-5 h-5 text-sky-400" />
                  {selectedPatient.full_name}
                </h3>
                <span className="text-xs text-slate-400 font-mono">Patient Record ID: {selectedPatient.id}</span>
              </div>
              <button
                onClick={() => setSelectedPatient(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Demographics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block font-semibold">Blood Group</span>
                <span className="text-rose-400 font-bold text-sm">{selectedPatient.blood_group || 'Unknown'}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Gender</span>
                <span className="text-white capitalize">{selectedPatient.gender || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Phone</span>
                <span className="text-white font-mono">{selectedPatient.phone || 'None'}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Email</span>
                <span className="text-white truncate block">{selectedPatient.email}</span>
              </div>
            </div>

            {/* Past Clinical Visits */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-teal-400" />
                Clinical Consultations & Visit History ({visits.length})
              </h4>

              {visits.length === 0 ? (
                <div className="p-8 text-center bg-slate-950/60 rounded-xl border border-slate-800 text-slate-500 text-xs">
                  No previous consultation records logged for this patient.
                </div>
              ) : (
                <div className="space-y-3">
                  {visits.map((v) => (
                    <div key={v.id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">
                          Dr. {v.doctor_name || 'Physician'} ({v.department_name || 'OPD'})
                        </span>
                        <span className="text-slate-400">{v.visit_date}</span>
                      </div>
                      {v.vitals_summary && (
                        <div className="text-slate-400 font-mono text-[11px] bg-slate-900 p-2 rounded border border-slate-800">
                          {v.vitals_summary}
                        </div>
                      )}
                      {v.administrative_notes && (
                        <p className="text-slate-300"><span className="text-slate-500">Notes:</span> {v.administrative_notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedPatient(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


