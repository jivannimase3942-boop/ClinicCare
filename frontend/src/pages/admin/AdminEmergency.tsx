import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { emergencyApi } from '@/services/emergencies'
import { Badge } from '@/components/ui/Badge'
import { Siren, AlertTriangle, CheckCircle2, Clock, Truck, ShieldAlert, Activity } from 'lucide-react'

export const AdminEmergency: React.FC = () => {
  const { data: statsData } = useQuery({
    queryKey: ['admin-emergency-stats'],
    queryFn: () => emergencyApi.getStats(),
  })

  const { data: emergenciesData, isLoading } = useQuery({
    queryKey: ['admin-emergencies'],
    queryFn: () => emergencyApi.getEmergencies(),
  })

  const stats = statsData?.data
  const emergencies = emergenciesData?.data || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Emergency & Critical Triage Board</h2>
        <p className="text-sm text-slate-400 mt-1">
          Real-time coordination for life-threatening emergencies, trauma intake, and hotline escalations.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <p className="text-xs font-semibold text-slate-400">Total Emergencies</p>
          <h3 className="text-2xl font-black text-white mt-1">{stats?.total_emergencies || 0}</h3>
        </div>

        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900/60">
          <p className="text-xs font-semibold text-rose-300">Critical Active</p>
          <h3 className="text-2xl font-black text-rose-400 mt-1">{stats?.critical_active || 0}</h3>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <p className="text-xs font-semibold text-slate-400">Dispatched Ambulances</p>
          <h3 className="text-2xl font-black text-sky-400 mt-1">{stats?.dispatched_ambulances || 0}</h3>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <p className="text-xs font-semibold text-slate-400">Avg Response Time</p>
          <h3 className="text-2xl font-black text-teal-400 mt-1">{stats?.average_response_minutes || 4.5}m</h3>
        </div>
      </div>

      {/* Emergency List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-rose-500" />
            Live Emergency Incident Stream ({emergencies.length})
          </h3>
        </div>

        <div className="divide-y divide-slate-800/60">
          {emergencies.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <Siren className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm font-bold">No active emergency incidents reported</p>
            </div>
          ) : (
            emergencies.map((e) => (
              <div key={e.id} className="p-4 hover:bg-slate-800/30 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">
                      {e.priority.toUpperCase()}
                    </span>
                    <span className="text-sm font-bold text-white">{e.caller_name}</span>
                    <span className="text-xs text-slate-400">({e.caller_phone})</span>
                  </div>
                  <Badge variant={e.status === 'resolved' ? 'success' : 'warning'}>{e.status}</Badge>
                </div>

                <div className="text-xs text-slate-300 grid grid-cols-1 md:grid-cols-2 gap-2">
                  <p><span className="text-slate-500 font-medium">Type:</span> {e.emergency_type}</p>
                  <p><span className="text-slate-500 font-medium">Location:</span> {e.location}</p>
                </div>

                {e.resolution_notes && (
                  <p className="text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                    <span className="font-semibold text-slate-300">Incident Log: </span>{e.resolution_notes}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
