import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { AlertTriangle } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

export const AdminErrors: React.FC = () => {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['admin-errors'],
    queryFn: () => adminService.getErrorLogs(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">System Error & Fault Logs</h1>
        <p className="text-xs text-slate-400">Real-time monitoring of backend, AI, and workflow exceptions</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading error logs...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-emerald-400 text-xs bg-slate-800/50 rounded-2xl border border-slate-700">
          All systems operational. No recorded errors!
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => (
            <div key={log.id} className="bg-slate-800/80 border border-rose-900/40 rounded-2xl p-4 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span className="font-bold text-white uppercase">{log.service_name}</span>
                  <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono">{log.error_level}</span>
                </div>
                <span className="text-slate-400">{formatDateTime(log.created_at)}</span>
              </div>
              <p className="text-rose-200 font-semibold">{log.message}</p>
              {log.stack_trace && (
                <pre className="p-3 bg-slate-900/90 rounded-xl text-[11px] font-mono text-slate-400 overflow-x-auto border border-slate-700">
                  {log.stack_trace}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
