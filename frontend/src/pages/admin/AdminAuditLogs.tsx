import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  Search,
  Filter,
  RefreshCw,
  Clock,
  User,
  Activity,
  Calendar,
  AlertTriangle,
  Lock,
} from 'lucide-react'
import { clinicService } from '@/services/clinic'
import { AuditLog } from '@/types'
import { useToast } from '@/context/ToastContext'

const ACTION_FILTERS = [
  'ALL',
  'LOGIN',
  'APPOINTMENT_CREATE',
  'CLINIC_ONBOARDED',
  'STAFF_APPROVED',
  'SYSTEM_INIT',
]

export const AdminAuditLogs: React.FC = () => {
  const { showToast } = useToast()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const fetchLogs = async () => {
    setIsLoading(true)
    try {
      const actionParam = selectedFilter === 'ALL' ? undefined : selectedFilter
      const data = await clinicService.getAuditLogs({ action: actionParam, limit: 100 })
      setLogs(data)
    } catch (err: any) {
      showToast('Failed to load audit logs', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [selectedFilter])

  const filteredLogs = logs.filter((l) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      l.action.toLowerCase().includes(q) ||
      (l.user_email && l.user_email.toLowerCase().includes(q)) ||
      (l.user_role && l.user_role.toLowerCase().includes(q)) ||
      (l.details && l.details.toLowerCase().includes(q))
    )
  })

  const getActionBadgeColor = (action: string) => {
    switch (action.toUpperCase()) {
      case 'LOGIN':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30'
      case 'CLINIC_ONBOARDED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
      case 'STAFF_APPROVED':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30'
      case 'APPOINTMENT_CREATE':
      case 'APPOINTMENT_STATUS_UPDATE':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/30'
      case 'SYSTEM_INIT':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <ShieldCheck className="w-7 h-7 text-emerald-400" /> Security & Operational Audit Logs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Immutable, tenant-isolated audit trail for clinical actions, user sessions, and governance.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          disabled={isLoading}
          className="self-start sm:self-auto px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Audit Trail
        </button>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
        {/* Action Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {ACTION_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setSelectedFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedFilter === f
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search email, action, details..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs">Decrypting audit stream...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-slate-500 space-y-2">
            <Lock className="w-8 h-8 mx-auto text-slate-600 mb-2" />
            <p className="text-sm font-medium text-slate-400">No audit entries found matching the filter.</p>
            <p className="text-xs">All significant administrative and clinical events will appear here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-900/60 text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">User & Role</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Details</th>
                  <th className="py-3 px-4">Client IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400 font-mono">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${getActionBadgeColor(
                          log.action
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-200">{log.user_email || 'System / Anonymous'}</div>
                      {log.user_role && (
                        <span className="text-[10px] text-slate-500 uppercase">{log.user_role}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                      {log.entity_type ? `${log.entity_type} ${log.entity_id ? `(#${log.entity_id.slice(0, 8)})` : ''}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate" title={log.details || ''}>
                      {log.details || '-'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px] text-slate-500">
                      {log.ip_address || 'Internal'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
