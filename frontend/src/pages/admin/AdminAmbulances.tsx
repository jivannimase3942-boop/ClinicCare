import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ambulanceApi } from '@/services/ambulances'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { Truck, Siren, MapPin, PhoneCall } from 'lucide-react'

export const AdminAmbulances: React.FC = () => {
  const { showToast } = useToast()
  const queryClient = useQueryClient()

  const { data: fleetData } = useQuery({
    queryKey: ['admin-ambulances'],
    queryFn: () => ambulanceApi.getAmbulances(),
  })

  const { data: requestsData } = useQuery({
    queryKey: ['admin-ambulance-requests'],
    queryFn: () => ambulanceApi.getRequests(),
  })

  const ambulances = fleetData?.data || []
  const requests = requestsData?.data || []

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, ambulanceId }: { id: string; status: string; ambulanceId?: string }) =>
      ambulanceApi.updateRequestStatus(id, { status, ambulance_id: ambulanceId }),
    onSuccess: () => {
      showToast('success', 'Request status updated!')
      queryClient.invalidateQueries({ queryKey: ['admin-ambulance-requests'] })
      queryClient.invalidateQueries({ queryKey: ['admin-ambulances'] })
    },
  })

  const updateAmbulanceMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      ambulanceApi.updateAmbulanceStatus(id, { status }),
    onSuccess: () => {
      showToast('success', 'Ambulance vehicle status updated!')
      queryClient.invalidateQueries({ queryKey: ['admin-ambulances'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Ambulance Fleet & Emergency Dispatch</h2>
        <p className="text-sm text-slate-400 mt-1">
          Real-time fleet status, emergency dispatch queue, and paramedic assignment.
        </p>
      </div>

      {/* Fleet Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ambulances.map((amb) => (
          <div key={amb.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-sky-400">{amb.vehicle_number}</span>
              <Badge variant={amb.status === 'available' ? 'success' : amb.status === 'busy' ? 'warning' : 'neutral'}>
                {amb.status.toUpperCase()}
              </Badge>
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">{amb.model}</h4>
              <p className="text-xs text-slate-400 mt-0.5">{amb.ambulance_type}</p>
            </div>
            <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800">
              <p className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-500" /> {amb.current_location}</p>
              <p className="flex items-center gap-1.5"><PhoneCall className="w-3.5 h-3.5 text-slate-500" /> {amb.driver_name || 'Driver'} ({amb.driver_phone || 'Direct'})</p>
            </div>
            <button
              onClick={() => updateAmbulanceMutation.mutate({ id: amb.id, status: amb.status === 'available' ? 'busy' : 'available' })}
              className="w-full py-1.5 rounded-lg text-xs font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              Toggle {amb.status === 'available' ? 'Busy' : 'Available'}
            </button>
          </div>
        ))}
      </div>

      {/* Requests Dispatch Queue Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Siren className="w-4 h-4 text-rose-500" />
            Active Ambulance Dispatch Requests ({requests.length})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Caller & Phone</th>
                <th className="p-3">Pickup Address</th>
                <th className="p-3">Priority</th>
                <th className="p-3">Assigned Vehicle</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {requests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    <Truck className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                    <p className="font-semibold text-slate-300">No active ambulance dispatch requests</p>
                    <p className="text-slate-500 text-xs mt-1">New incoming ambulance requests from patients or hotline will appear here.</p>
                  </td>
                </tr>
              ) : (
                requests.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40">
                  <td className="p-3">
                    <span className="font-bold text-white block">{r.requester_name}</span>
                    <span className="text-slate-400 font-mono text-[11px]">{r.requester_phone}</span>
                  </td>
                  <td className="p-3 max-w-xs truncate">{r.pickup_address}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.emergency_priority === 'critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'}`}>
                      {r.emergency_priority.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-sky-400">{r.ambulance_vehicle_number || 'Unassigned'}</td>
                  <td className="p-3">
                    <Badge variant={r.status === 'completed' ? 'success' : r.status === 'en_route' ? 'warning' : 'neutral'}>
                      {r.status}
                    </Badge>
                  </td>
                  <td className="p-3 text-right space-x-1">
                    {r.status === 'requested' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'assigned', ambulanceId: ambulances[0]?.id })}
                        className="px-2.5 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs"
                      >
                        Assign Unit
                      </button>
                    )}
                    {r.status === 'assigned' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'en_route' })}
                        className="px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs"
                      >
                        En Route
                      </button>
                    )}
                    {r.status === 'en_route' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ id: r.id, status: 'completed' })}
                        className="px-2.5 py-1 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs"
                      >
                        Complete
                      </button>
                    )}
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
