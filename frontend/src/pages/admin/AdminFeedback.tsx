import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { Star, User } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const AdminFeedback: React.FC = () => {
  const { data: feedbacks = [], isLoading } = useQuery({
    queryKey: ['admin-feedback'],
    queryFn: () => adminService.getFeedback(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Patient Reviews & Satisfaction</h1>
        <p className="text-xs text-slate-400">Total reviews submitted: {feedbacks.length}</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading feedback...</div>
      ) : feedbacks.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-xs">No feedback recorded yet.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {feedbacks.map((f) => (
            <div key={f.id} className="bg-slate-800/80 border border-slate-700 rounded-2xl p-4 space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-slate-300">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">{f.patient_name || 'Anonymous Patient'}</h4>
                    <span className="text-[10px] text-slate-400">{formatDate(f.created_at)}</span>
                  </div>
                </div>
                <div className="flex text-amber-400">
                  {Array.from({ length: f.rating }).map((_, i) => (
                    <Star key={i} className="w-3.5 h-3.5 fill-amber-400" />
                  ))}
                </div>
              </div>
              {f.comment && (
                <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-700/50">
                  "{f.comment}"
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
