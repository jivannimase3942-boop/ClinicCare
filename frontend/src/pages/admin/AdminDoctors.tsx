import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Stethoscope, Award, MapPin } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

export const AdminDoctors: React.FC = () => {
  const { data: doctors = [], isLoading } = useQuery({
    queryKey: ['admin-doctors'],
    queryFn: () => adminService.getDoctors(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Doctors & Medical Specialists</h1>
        <p className="text-xs text-slate-400">Manage hospital clinicians, OPD slots, and consulting fees</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading doctors...</div>
      ) : doctors.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No doctors currently registered.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {doctors.map((doc) => (
            <div key={doc.id} className="bg-slate-800/80 border border-slate-700 rounded-2xl p-5 space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">{doc.full_name}</h3>
                  <p className="text-xs text-sky-400 font-semibold">{doc.specialization}</p>
                  <p className="text-xs text-slate-400">{doc.department_name}</p>
                </div>
              </div>

              <div className="space-y-1 text-xs text-slate-300 border-t border-slate-700/60 pt-2.5">
                <p className="flex items-center gap-1.5"><Award className="w-3.5 h-3.5 text-amber-400" /> {doc.qualification} • {doc.experience_years} yrs</p>
                <p className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-400" /> {doc.location}</p>
              </div>

              <div className="border-t border-slate-700/60 pt-2.5 flex justify-between items-center text-xs">
                <span className="text-slate-400">Consultation Fee</span>
                <span className="font-bold text-teal-400 text-sm">{formatCurrency(doc.consultation_fee)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
