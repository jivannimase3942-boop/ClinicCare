import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appointmentService, WalkInPayload } from '@/services/appointments'
import { doctorService } from '@/services/doctors'
import { Appointment, Doctor, WaitlistEntry } from '@/types'
import {
  Users,
  Ticket,
  Clock,
  CheckCircle2,
  PhoneCall,
  UserPlus,
  Play,
  RotateCcw,
  Search,
  Filter,
  ArrowRight,
  Calendar,
} from 'lucide-react'
import { useToast } from '@/context/ToastContext'

export const FrontDeskQueue: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [isWalkInModalOpen, setIsWalkInModalOpen] = useState(false)
  const [isWaitlistModalOpen, setIsWaitlistModalOpen] = useState(false)

  // Walk-in form state
  const [walkInName, setWalkInName] = useState('')
  const [walkInPhone, setWalkInPhone] = useState('')
  const [walkInDocId, setWalkInDocId] = useState('')
  const [walkInReason, setWalkInReason] = useState('')
  const [walkInType, setWalkInType] = useState('NEW_CONSULTATION')

  // 1. Fetch Doctors
  const { data: doctors = [] } = useQuery<Doctor[]>({
    queryKey: ['frontdesk-doctors'],
    queryFn: () => doctorService.getDoctors(),
  })

  // 2. Fetch Today's Queue
  const { data: queue = [], isLoading: isQueueLoading } = useQuery<Appointment[]>({
    queryKey: ['frontdesk-today-queue', selectedDoctorId],
    queryFn: () => appointmentService.getTodayQueue(selectedDoctorId || undefined),
    refetchInterval: 10000,
  })

  // 3. Fetch Waitlist
  const { data: waitlist = [] } = useQuery<WaitlistEntry[]>({
    queryKey: ['frontdesk-waitlist', selectedDoctorId],
    queryFn: () => appointmentService.getWaitlist({ doctor_id: selectedDoctorId || undefined }),
    refetchInterval: 20000,
  })

  // 4. Mutations
  const walkInMutation = useMutation({
    mutationFn: (payload: WalkInPayload) => appointmentService.createWalkIn(payload),
    onSuccess: (data) => {
      showToast(`Walk-in confirmed. Token: ${data.token_number}`, 'success')
      queryClient.invalidateQueries({ queryKey: ['frontdesk-today-queue'] })
      setIsWalkInModalOpen(false)
      setWalkInName('')
      setWalkInPhone('')
      setWalkInReason('')
    },
    onError: (err: any) => {
      showToast(err?.response?.data?.message || err?.response?.data?.detail || 'Walk-in booking failed', 'error')
    },
  })

  const queueUpdateMutation = useMutation({
    mutationFn: (payload: { id: string; status: string }) =>
      appointmentService.updateQueue(payload.id, payload.status),
    onSuccess: () => {
      showToast('Queue status updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['frontdesk-today-queue'] })
    },
    onError: (err: any) => {
      showToast(err?.response?.data?.message || 'Queue update failed', 'error')
    },
  })

  const checkInMutation = useMutation({
    mutationFn: (id: string) => appointmentService.checkIn(id),
    onSuccess: (data) => {
      showToast(`Checked in. Token: ${data.token_number}`, 'success')
      queryClient.invalidateQueries({ queryKey: ['frontdesk-today-queue'] })
    },
    onError: (err: any) => {
      showToast(err?.response?.data?.message || 'Check-in failed', 'error')
    },
  })

  const handleWalkInSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!walkInDocId) {
      showToast('Please select a doctor', 'error')
      return
    }
    walkInMutation.mutate({
      doctor_id: walkInDocId,
      patient_name: walkInName,
      patient_phone: walkInPhone,
      reason: walkInReason,
      appointment_type: walkInType,
    })
  }

  const filteredQueue = queue.filter((item) => {
    const term = searchTerm.toLowerCase()
    return (
      (item.patient_name && item.patient_name.toLowerCase().includes(term)) ||
      (item.token_number && item.token_number.toLowerCase().includes(term)) ||
      (item.doctor_name && item.doctor_name.toLowerCase().includes(term))
    )
  })

  const waitingCount = queue.filter((q) => q.queue_status === 'WAITING').length
  const calledCount = queue.filter((q) => q.queue_status === 'CALLED').length
  const inConsultCount = queue.filter((q) => q.queue_status === 'IN_CONSULTATION').length

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Reception Queue Control
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Today's OPD Queue & Tokens</h1>
          <p className="text-xs text-slate-400 mt-1">
            Generate tokens, check in arriving patients, manage live queue transitions, and review waitlist.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsWalkInModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950/30 transition active:scale-95"
          >
            <UserPlus className="w-4 h-4" />
            Issue Walk-in Token
          </button>
        </div>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium uppercase">Waiting in Lounge</p>
            <p className="text-2xl font-black text-amber-400 mt-0.5">{waitingCount}</p>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium uppercase">Called into OPD</p>
            <p className="text-2xl font-black text-sky-400 mt-0.5">{calledCount}</p>
          </div>
          <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400">
            <PhoneCall className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium uppercase">In Consultation</p>
            <p className="text-2xl font-black text-emerald-400 mt-0.5">{inConsultCount}</p>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
            <Play className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-400 font-medium uppercase">Active Waitlist</p>
            <p className="text-2xl font-black text-purple-400 mt-0.5">{waitlist.length}</p>
          </div>
          <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
            <Ticket className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Queue Filter & Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden p-5 space-y-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Ticket className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-bold text-white">Live Patient Queue</h2>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Filter by Doctor */}
            <select
              value={selectedDoctorId}
              onChange={(e) => setSelectedDoctorId(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500"
            >
              <option value="">All On-Duty Doctors</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name} ({d.specialization})
                </option>
              ))}
            </select>

            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search token / patient..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500 placeholder-slate-500"
              />
            </div>
          </div>
        </div>

        {/* Queue Table */}
        <div className="overflow-x-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-800/80 text-slate-400 font-semibold border-b border-slate-700">
                <th className="py-3 px-4">Token</th>
                <th className="py-3 px-4">Patient</th>
                <th className="py-3 px-4">Doctor</th>
                <th className="py-3 px-4">Slot Time</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Queue Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {filteredQueue.length > 0 ? (
                filteredQueue.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4">
                      {item.token_number ? (
                        <span className="inline-block px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-bold text-xs">
                          {item.token_number}
                        </span>
                      ) : (
                        <button
                          onClick={() => checkInMutation.mutate(item.id)}
                          className="px-2 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-[11px] font-medium"
                        >
                          Check In & Token
                        </button>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{item.patient_name || 'Patient'}</div>
                      <div className="text-[11px] text-slate-500">{item.patient_phone || ''}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-200">{item.doctor_name || 'Physician'}</div>
                      <div className="text-[10px] text-slate-500">{item.department_name}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{item.appointment_time}</td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                        {item.appointment_type?.replace('_', ' ') || 'OPD'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          item.queue_status === 'WAITING'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : item.queue_status === 'CALLED'
                            ? 'bg-sky-500/10 text-sky-400 border-sky-500/20'
                            : item.queue_status === 'IN_CONSULTATION'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : item.queue_status === 'COMPLETED'
                            ? 'bg-slate-700 text-slate-300 border-slate-600'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {item.queue_status || 'NOT QUEUED'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {item.queue_status === 'WAITING' && (
                          <button
                            onClick={() => queueUpdateMutation.mutate({ id: item.id, status: 'CALLED' })}
                            className="px-2 py-1 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-medium text-[11px]"
                          >
                            Call
                          </button>
                        )}
                        {item.queue_status === 'CALLED' && (
                          <button
                            onClick={() => queueUpdateMutation.mutate({ id: item.id, status: 'IN_CONSULTATION' })}
                            className="px-2 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[11px]"
                          >
                            In OPD
                          </button>
                        )}
                        {item.queue_status === 'IN_CONSULTATION' && (
                          <button
                            onClick={() => queueUpdateMutation.mutate({ id: item.id, status: 'COMPLETED' })}
                            className="px-2 py-1 rounded-md bg-slate-700 hover:bg-slate-600 text-white font-medium text-[11px]"
                          >
                            Complete
                          </button>
                        )}
                        {item.queue_status === 'WAITING' && (
                          <button
                            onClick={() => queueUpdateMutation.mutate({ id: item.id, status: 'SKIPPED' })}
                            className="px-2 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white font-medium text-[11px]"
                          >
                            Skip
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No patients queued for today.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Walk-In Modal */}
      {isWalkInModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Issue Walk-in OPD Token</h3>
                <p className="text-xs text-slate-400">Register arriving patient and add to doctor queue</p>
              </div>
              <button
                onClick={() => setIsWalkInModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleWalkInSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Patient Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={walkInName}
                  onChange={(e) => setWalkInName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Phone Number</label>
                <input
                  type="tel"
                  required
                  placeholder="+91 98765 43210"
                  value={walkInPhone}
                  onChange={(e) => setWalkInPhone(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Attending Doctor</label>
                <select
                  required
                  value={walkInDocId}
                  onChange={(e) => setWalkInDocId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500 text-xs"
                >
                  <option value="">Select Doctor...</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name} ({d.specialization}) - Room {d.location || 'OPD'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Consultation Type</label>
                <select
                  value={walkInType}
                  onChange={(e) => setWalkInType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500 text-xs"
                >
                  <option value="NEW_CONSULTATION">New Consultation</option>
                  <option value="FOLLOW_UP">Follow-up Visit</option>
                  <option value="PROCEDURE">Minor Procedure / Dressing</option>
                  <option value="EMERGENCY">Emergency Triage</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Chief Complaint / Reason</label>
                <input
                  type="text"
                  placeholder="e.g. Fever, persistent cough"
                  value={walkInReason}
                  onChange={(e) => setWalkInReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsWalkInModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={walkInMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold disabled:opacity-50"
                >
                  {walkInMutation.isPending ? 'Issuing Token...' : 'Issue Token'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default FrontDeskQueue
