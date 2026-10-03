import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { clinicalService } from '@/services/clinical'
import { useAuth } from '@/context/AuthContext'
import { Card, CardTitle, CardHeader, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import {
  Activity,
  Stethoscope,
  Calendar,
  FileText,
  Clock,
  Heart,
  User,
  ShieldCheck,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const PatientTimelinePage: React.FC = () => {
  const { user } = useAuth()
  const patientId = user?.patient_profile?.id || ''

  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ['patient-timeline', patientId],
    queryFn: () => clinicalService.getPatientTimeline(patientId),
    enabled: !!patientId,
  })

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-teal-700 to-sky-800 rounded-3xl p-6 text-white space-y-2">
        <div className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-teal-300" />
          <span className="text-xs uppercase tracking-wider font-semibold text-teal-200">
            Longitudinal Health Record
          </span>
        </div>
        <h1 className="text-2xl font-black">My Medical Timeline</h1>
        <p className="text-xs text-teal-100">
          Chronological record of verified clinical consultations, vital sign trends, visits, and reports
        </p>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-xs text-slate-500">Loading your medical timeline...</div>
      ) : error ? (
        <Card className="p-8 text-center text-xs text-red-600 bg-red-50 border-red-200">
          Failed to load medical timeline. Please try again.
        </Card>
      ) : !timeline || timeline.events.length === 0 ? (
        <Card className="py-16 text-center text-slate-500 space-y-2">
          <Stethoscope className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="font-semibold text-sm text-slate-700">No clinical events recorded yet</p>
          <p className="text-xs text-slate-400">
            Consultations, recorded vitals, and reports will appear here as they occur.
          </p>
        </Card>
      ) : (
        <div className="relative border-l-2 border-teal-200 ml-4 pl-6 space-y-8 py-2">
          {timeline.events.map((event, idx) => {
            const isConsult = event.event_type === 'CONSULTATION'
            const isVital = event.event_type === 'VITAL_SIGN'
            const isAppt = event.event_type === 'APPOINTMENT'
            const isDoc = event.event_type === 'DOCUMENT'

            return (
              <div key={idx} className="relative group">
                {/* Timeline Icon Node */}
                <div
                  className={`absolute -left-[35px] top-1.5 w-7 h-7 rounded-full flex items-center justify-center text-white border-2 border-white shadow-sm ${
                    isConsult ? 'bg-teal-600' :
                    isVital ? 'bg-rose-500' :
                    isAppt ? 'bg-sky-600' : 'bg-purple-600'
                  }`}
                >
                  {isConsult && <Stethoscope className="w-3.5 h-3.5" />}
                  {isVital && <Activity className="w-3.5 h-3.5" />}
                  {isAppt && <Calendar className="w-3.5 h-3.5" />}
                  {isDoc && <FileText className="w-3.5 h-3.5" />}
                </div>

                {/* Event Card */}
                <Card className="p-5 space-y-3 transition-shadow hover:shadow-md border-slate-200">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-black uppercase tracking-wider text-slate-500">
                        {event.event_type.replace('_', ' ')}
                      </span>
                      {event.status && (
                        <Badge
                          variant={
                            event.status === 'FINALIZED' || event.status === 'completed'
                              ? 'success'
                              : 'default'
                          }
                          className="text-[10px]"
                        >
                          {event.status}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(event.timestamp).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{event.title}</h3>
                    {event.subtitle && (
                      <p className="text-xs text-slate-600 mt-0.5">{event.subtitle}</p>
                    )}
                  </div>

                  {/* Doctor Context */}
                  {event.doctor_name && (
                    <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-2 rounded-xl border border-slate-100">
                      <User className="w-3.5 h-3.5 text-teal-600" />
                      <span>Attending Physician: <strong>{event.doctor_name}</strong></span>
                      {event.department_name && <span>({event.department_name})</span>}
                    </div>
                  )}

                  {/* Extra Details */}
                  {isConsult && event.details?.treatment_plan && (
                    <div className="text-xs p-3 bg-teal-50 border border-teal-100 rounded-xl space-y-1">
                      <p className="font-bold text-teal-900">Treatment Plan / Prescription Guidance:</p>
                      <p className="text-teal-800">{event.details.treatment_plan}</p>
                      {event.details.follow_up_date && (
                        <p className="text-teal-700 text-[11px] pt-1">
                          📅 Follow-up advised on: <strong>{formatDate(event.details.follow_up_date)}</strong>
                        </p>
                      )}
                    </div>
                  )}

                  {isVital && event.details?.bmi && (
                    <div className="text-xs text-slate-600">
                      Body Mass Index (BMI): <strong>{event.details.bmi} kg/m²</strong>
                      {event.details.weight_kg && ` • Weight: ${event.details.weight_kg} kg`}
                      {event.details.height_cm && ` • Height: ${event.details.height_cm} cm`}
                    </div>
                  )}
                </Card>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
