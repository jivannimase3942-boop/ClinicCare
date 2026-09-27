import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { patientsApi } from '@/services/patients'
import { useAuth } from '@/context/AuthContext'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Activity, Calendar, Stethoscope, FileText, CheckCircle2, ClipboardCheck } from 'lucide-react'

export const VisitHistoryPage: React.FC = () => {
  const { user } = useAuth()
  const patientId = user?.patient_profile?.id

  const { data, isLoading } = useQuery({
    queryKey: ['my-visits', patientId],
    queryFn: () => (patientId ? patientsApi.getPatientVisits(patientId) : Promise.resolve({ success: true, data: [] })),
    enabled: !!patientId,
  })

  const visits = data?.data || []

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-teal-700 to-emerald-700 rounded-2xl p-6 text-white shadow-lg flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 border border-white/20">
          <ClipboardCheck className="w-7 h-7 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-black tracking-tight">Patient Consultation & Visit History</h2>
          <p className="text-xs text-teal-100 mt-0.5">
            Complete record of your hospital visits, physician consults, vital stats, and follow-up guidance.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="w-5 h-5 text-teal-600" />
            Past Consultations Timeline ({visits.length} records)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          {visits.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-bold text-slate-700">No past clinical visits recorded</p>
              <p className="text-xs text-slate-500 mt-1">Completed OPD visits and consultations will appear in this log.</p>
            </div>
          ) : (
            <div className="space-y-5">
              {visits.map((v) => (
                <div key={v.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/70 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xs">
                        <Calendar className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          {v.doctor_name || 'Attending Physician'}
                          <span className="text-xs font-normal text-slate-500">({v.department_name || 'General OPD'})</span>
                        </h4>
                        <p className="text-xs text-slate-500">Visit Date: {v.visit_date} • {v.visit_type}</p>
                      </div>
                    </div>
                    <Badge variant="success" className="w-fit">Completed Consultation</Badge>
                  </div>

                  {v.vitals_summary && (
                    <div className="bg-white p-3 rounded-lg border border-slate-200/80 text-xs">
                      <span className="font-bold text-slate-700 block mb-0.5">Recorded Vitals:</span>
                      <span className="text-slate-600 font-mono">{v.vitals_summary}</span>
                    </div>
                  )}

                  {v.administrative_notes && (
                    <div className="text-xs text-slate-600">
                      <span className="font-bold text-slate-700">Clinical / Billing Notes: </span>
                      {v.administrative_notes}
                    </div>
                  )}

                  {v.follow_up_instructions && (
                    <div className="text-xs text-teal-800 bg-teal-50/80 p-2.5 rounded-lg border border-teal-100 font-medium">
                      <span className="font-bold">Follow-Up Instructions: </span>
                      {v.follow_up_instructions}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
