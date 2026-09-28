import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Stethoscope, Award, MapPin, ShieldCheck, Clock, CheckCircle2, UserCheck, AlertCircle } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { useToast } from '@/context/ToastContext'

export const AdminDoctors: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data: doctors = [], isLoading: isLoadingDoctors } = useQuery({
    queryKey: ['admin-doctors'],
    queryFn: () => adminService.getDoctors(),
  })

  const { data: pendingStaff = [], isLoading: isLoadingPending } = useQuery({
    queryKey: ['admin-pending-staff'],
    queryFn: () => adminService.getPendingStaff(),
  })

  const approveMutation = useMutation({
    mutationFn: (userId: string) => adminService.approvePendingStaff(userId),
    onSuccess: (data) => {
      showToast(data.message || 'Staff member verified and approved!', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-pending-staff'] })
      queryClient.invalidateQueries({ queryKey: ['admin-doctors'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError: (err: any) => {
      showToast(err.response?.data?.detail || 'Failed to approve staff', 'error')
    },
  })

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Doctors & Medical Specialists</h1>
        <p className="text-xs text-slate-400">Manage hospital clinicians, OPD slots, consulting fees, and pending credentials</p>
      </div>

      {/* Pending Staff Verification Requests */}
      {pendingStaff.length > 0 && (
        <div className="bg-amber-950/20 border border-amber-800/40 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-400 animate-pulse" />
              <div>
                <h2 className="text-sm font-bold text-white">Pending Staff Access Requests ({pendingStaff.length})</h2>
                <p className="text-xs text-slate-400">Clinicians and front desk personnel awaiting administrative verification</p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Action Required
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingStaff.map((staff) => (
              <div
                key={staff.id}
                className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 flex flex-col justify-between gap-3 shadow-md"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">{staff.full_name}</h3>
                      <p className="text-xs text-slate-400">{staff.email} • {staff.phone}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-sky-400 border border-slate-700">
                      {staff.role === 'PENDING_DOCTOR' ? 'Doctor Request' : 'Front Desk Request'}
                    </span>
                  </div>

                  {staff.doctor_profile && (
                    <div className="mt-2.5 pt-2.5 border-t border-slate-800 text-xs text-slate-300 space-y-1">
                      <p><span className="text-slate-400">Specialization:</span> <span className="text-white font-medium">{staff.doctor_profile.specialization}</span></p>
                      <p><span className="text-slate-400">License No:</span> <span className="font-mono text-amber-300">{staff.doctor_profile.license_number || 'N/A'}</span></p>
                      <p><span className="text-slate-400">Qualification:</span> {staff.doctor_profile.qualification}</p>
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-800 flex justify-end">
                  <button
                    disabled={approveMutation.isPending}
                    onClick={() => approveMutation.mutate(staff.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition disabled:opacity-50"
                  >
                    <UserCheck className="w-3.5 h-3.5" />
                    {approveMutation.isPending ? 'Approving...' : 'Verify & Approve'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Doctors Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Stethoscope className="w-4 h-4 text-teal-400" />
          Active Hospital Clinicians
        </h2>

        {isLoadingDoctors ? (
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
    </div>
  )
}
