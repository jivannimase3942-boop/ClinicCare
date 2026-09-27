import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bloodApi } from '@/services/blood'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Droplet, Plus, Minus, Building, PhoneCall, MapPin, Search, CheckCircle2, ShieldCheck, ClipboardList } from 'lucide-react'

export const AdminBloodBank: React.FC = () => {
  const { showToast } = useToast()
  const queryClient = useQueryClient()
  const [filterStatus, setFilterStatus] = useState('')
  const [filterGroup, setFilterGroup] = useState('')
  const [matchingRequestId, setMatchingRequestId] = useState<string | null>(null)
  const [selectedBankId, setSelectedBankId] = useState<string>('')
  const [matchNotes, setMatchNotes] = useState<string>('')

  const { data: banksData } = useQuery({
    queryKey: ['admin-blood-banks'],
    queryFn: () => bloodApi.getBanks(),
  })

  const { data: requestsData } = useQuery({
    queryKey: ['admin-blood-requests', filterStatus, filterGroup],
    queryFn: () =>
      bloodApi.getBloodRequests({
        status: filterStatus || undefined,
        blood_group: filterGroup || undefined,
      }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, units }: { id: string; units: number }) =>
      bloodApi.updateInventory(id, { units_available: Math.max(0, units) }),
    onSuccess: () => {
      showToast('success', 'Blood stock updated successfully!')
      queryClient.invalidateQueries({ queryKey: ['admin-blood-banks'] })
    },
    onError: () => {
      showToast('error', 'Failed to update blood stock')
    },
  })

  const updateRequestStatusMutation = useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: string; notes?: string }) =>
      bloodApi.updateBloodRequestStatus(id, { status, admin_notes: notes }),
    onSuccess: () => {
      showToast('success', 'Blood request status updated!')
      queryClient.invalidateQueries({ queryKey: ['admin-blood-requests'] })
    },
  })

  const matchBankMutation = useMutation({
    mutationFn: ({ requestId, bankId, notes }: { requestId: string; bankId: string; notes?: string }) =>
      bloodApi.matchBloodBank(requestId, bankId, notes),
    onSuccess: () => {
      showToast('success', 'Blood bank matched and recorded!')
      setMatchingRequestId(null)
      setSelectedBankId('')
      setMatchNotes('')
      queryClient.invalidateQueries({ queryKey: ['admin-blood-requests'] })
    },
  })

  const bloodBanks = banksData?.data || []
  const requests = requestsData?.data || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Blood Bank Inventory & Reserves</h2>
        <p className="text-sm text-slate-400 mt-1">
          Monitor real-time blood group stock levels and component reserves across hospital banks.
        </p>
      </div>

      <div className="space-y-6">
        {bloodBanks.map((bank) => (
          <div key={bank.id} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Building className="w-4 h-4 text-rose-500" />
                  {bank.name}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{bank.address}, {bank.city} • {bank.phone}</p>
              </div>
              <Badge variant="success">Verified Reserve</Badge>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
              {bank.inventory.map((inv) => (
                <div
                  key={inv.id}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-between space-y-2 text-center"
                >
                  <span className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center font-black text-sm">
                    {inv.blood_group}
                  </span>

                  <div>
                    <span className="text-lg font-black text-white">{inv.units_available}</span>
                    <span className="text-[10px] text-slate-500 block uppercase">Units</span>
                  </div>

                  <div className="flex items-center gap-1 w-full pt-1">
                    <button
                      onClick={() => updateMutation.mutate({ id: inv.id, units: inv.units_available - 1 })}
                      className="flex-1 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs"
                    >
                      -
                    </button>
                    <button
                      onClick={() => updateMutation.mutate({ id: inv.id, units: inv.units_available + 1 })}
                      className="flex-1 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Blood Requests Management Section (Requirement 9) */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-rose-500" />
              Patient Blood Requirement Requests ({requests.length})
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Review incoming clinical requirements, search matching stock, and fulfill allocations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={filterGroup}
              onChange={(e) => setFilterGroup(e.target.value)}
              className="h-8 rounded-lg bg-slate-950 border border-slate-800 px-2.5 text-xs text-slate-300 focus:outline-none"
            >
              <option value="">All Groups</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-8 rounded-lg bg-slate-950 border border-slate-800 px-2.5 text-xs text-slate-300 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="searching">Searching</option>
              <option value="match_found">Match Found</option>
              <option value="fulfilled">Fulfilled</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Requests Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Req ID / Patient</th>
                  <th className="p-3">Group & Units</th>
                  <th className="p-3">Facility</th>
                  <th className="p-3">Urgency</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Matched Bank</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {requests.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40">
                    <td className="p-3">
                      <span className="font-mono text-[11px] text-slate-500 block">#{r.id.slice(0, 8)}</span>
                      <span className="font-bold text-white block">{r.patient_name}</span>
                      <span className="text-slate-400 font-mono text-[11px]">{r.contact_phone}</span>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-xs font-black bg-rose-950 text-rose-300 border border-rose-800">
                        {r.blood_group}
                      </span>
                      <span className="text-slate-300 font-bold ml-1.5">{r.units_required} unit(s)</span>
                    </td>
                    <td className="p-3">
                      <span className="text-white block font-medium">{r.hospital_clinic_name}</span>
                      <span className="text-slate-400 text-[11px]">{r.location}</span>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">
                        {r.urgency.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3">
                      <Badge variant={r.status === 'fulfilled' ? 'success' : r.status === 'match_found' ? 'primary' : 'warning'}>
                        {r.status}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <span className="text-teal-400 font-bold text-[11px]">{r.matched_bank_name || 'Unmatched'}</span>
                    </td>
                    <td className="p-3 text-right space-x-1 whitespace-nowrap">
                      {r.status === 'submitted' && (
                        <button
                          onClick={() => updateRequestStatusMutation.mutate({ id: r.id, status: 'searching' })}
                          className="px-2 py-1 rounded bg-amber-600 text-white font-bold text-xs"
                        >
                          Searching
                        </button>
                      )}
                      {(r.status === 'submitted' || r.status === 'searching') && (
                        <button
                          onClick={() => {
                            setMatchingRequestId(r.id)
                            setSelectedBankId(bloodBanks[0]?.id || '')
                          }}
                          className="px-2 py-1 rounded bg-sky-600 text-white font-bold text-xs"
                        >
                          Match Bank
                        </button>
                      )}
                      {r.status === 'match_found' && (
                        <button
                          onClick={() => updateRequestStatusMutation.mutate({ id: r.id, status: 'fulfilled', notes: 'Delivered' })}
                          className="px-2 py-1 rounded bg-teal-600 text-white font-bold text-xs"
                        >
                          Fulfill
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Match Blood Bank Modal */}
      {matchingRequestId && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-white">Record Matching Blood Bank</h3>
            <p className="text-xs text-slate-400">
              Select verified blood bank to match to request #{matchingRequestId.slice(0, 8)}.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Blood Bank *</label>
                <select
                  value={selectedBankId}
                  onChange={(e) => setSelectedBankId(e.target.value)}
                  className="w-full h-9 rounded-xl bg-slate-950 border border-slate-800 px-3 text-xs text-white focus:outline-none"
                >
                  {bloodBanks.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.city})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Notes</label>
                <Input
                  value={matchNotes}
                  onChange={(e) => setMatchNotes(e.target.value)}
                  placeholder="e.g. 2 units allocated"
                  className="text-xs h-9 bg-slate-950 border-slate-800 text-white"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setMatchingRequestId(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (matchingRequestId && selectedBankId) {
                    matchBankMutation.mutate({
                      requestId: matchingRequestId,
                      bankId: selectedBankId,
                      notes: matchNotes,
                    })
                  }
                }}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-bold hover:bg-rose-500"
              >
                Confirm Match
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
