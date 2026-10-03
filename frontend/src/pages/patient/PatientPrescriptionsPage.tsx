import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { prescriptionService } from '@/services/prescriptions'
import { useAuth } from '@/context/AuthContext'
import { Prescription } from '@/types'
import { Card, CardTitle, CardHeader, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import {
  Pill,
  Printer,
  Calendar,
  User,
  ShieldCheck,
  Eye,
  FileCheck2,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export const PatientPrescriptionsPage: React.FC = () => {
  const { user } = useAuth()
  const patientId = user?.patient_profile?.id || ''

  const [selectedRx, setSelectedRx] = useState<Prescription | null>(null)

  const { data: prescriptions = [], isLoading } = useQuery({
    queryKey: ['patient-prescriptions', patientId],
    queryFn: () => prescriptionService.listPatientPrescriptions(patientId, true),
    enabled: !!patientId,
  })

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-teal-700 to-sky-800 rounded-3xl p-6 text-white space-y-2">
        <div className="flex items-center gap-2">
          <Pill className="w-5 h-5 text-teal-300" />
          <span className="text-xs uppercase tracking-wider font-semibold text-teal-200">
            Verified Digital Healthcare
          </span>
        </div>
        <h1 className="text-2xl font-black">My Prescriptions</h1>
        <p className="text-xs text-teal-100">
          Physician-signed digital prescriptions, medication dosage guides, and treatment plans
        </p>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-xs text-slate-500">Loading your prescriptions...</div>
      ) : prescriptions.length === 0 ? (
        <Card className="py-16 text-center text-slate-500 space-y-2">
          <Pill className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="font-semibold text-sm text-slate-700">No prescriptions issued yet</p>
          <p className="text-xs text-slate-400">
            Prescriptions issued by your attending doctors will appear here.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {prescriptions.map((rx) => (
            <Card key={rx.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-slate-900 text-sm">{rx.prescription_number}</span>
                  <Badge variant="success" className="text-[10px]">
                    <ShieldCheck className="w-3 h-3 mr-1" /> {rx.status}
                  </Badge>
                  <span className="text-xs text-slate-400">
                    {formatDate(rx.created_at)}
                  </span>
                </div>
                <p className="text-xs font-semibold text-slate-700">
                  Diagnosis: {rx.diagnosis_summary}
                </p>
                <p className="text-xs text-slate-500">
                  Doctor: <strong>{rx.doctor_name || 'Attending Physician'}</strong> ({rx.doctor_specialization || 'General'})
                </p>
                <div className="flex items-center gap-2 text-xs text-teal-800 pt-1">
                  <Pill className="w-3.5 h-3.5" />
                  <span>{rx.items.length} prescribed medication(s)</span>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                className="self-start sm:self-center"
                leftIcon={<Eye className="w-4 h-4" />}
                onClick={() => setSelectedRx(rx)}
              >
                View & Print Rx
              </Button>
            </Card>
          ))}
        </div>
      )}

      {/* Printable Rx Modal */}
      {selectedRx && (
        <Modal
          isOpen={!!selectedRx}
          onClose={() => setSelectedRx(null)}
          title={`Prescription — ${selectedRx.prescription_number}`}
        >
          <div className="space-y-6 p-2 text-xs">
            {/* Clinic & Doctor Header */}
            <div className="border-b-2 border-teal-600 pb-4 flex justify-between items-start">
              <div>
                <h2 className="text-lg font-black text-slate-900">{selectedRx.clinic_name || 'ClinicCare Central'}</h2>
                <p className="text-slate-500">{selectedRx.clinic_address || 'Healthcare Boulevard'}</p>
                <p className="text-slate-500">Phone: {selectedRx.clinic_phone || '+91 80 2345 6789'}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-slate-900 text-sm">{selectedRx.doctor_name}</p>
                <p className="text-slate-600">{selectedRx.doctor_specialization}</p>
                <p className="text-slate-400">{selectedRx.doctor_qualification || 'MBBS, MD'}</p>
              </div>
            </div>

            {/* Patient Header */}
            <div className="bg-slate-50 p-3 rounded-xl border flex justify-between">
              <div>
                <p className="font-bold text-slate-800">Patient: {selectedRx.patient_name || user?.full_name}</p>
                <p className="text-slate-500">Phone: {selectedRx.patient_phone || user?.phone || 'N/A'}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-teal-800">Rx No: {selectedRx.prescription_number}</p>
                <p className="text-slate-500">Date: {new Date(selectedRx.created_at).toLocaleDateString()}</p>
              </div>
            </div>

            {/* Diagnosis */}
            <div>
              <span className="font-bold text-slate-700">Diagnosis: </span>
              <span className="text-slate-900 font-semibold">{selectedRx.diagnosis_summary}</span>
            </div>

            {/* Medication Table */}
            <div>
              <h4 className="font-black text-base text-slate-900 mb-2 font-serif">℞ Prescribed Medicines</h4>
              <table className="w-full text-left border-collapse border border-slate-200">
                <thead>
                  <tr className="bg-teal-50 border-b border-slate-200">
                    <th className="p-2">#</th>
                    <th className="p-2">Medicine</th>
                    <th className="p-2">Dosage</th>
                    <th className="p-2">Frequency</th>
                    <th className="p-2">Duration</th>
                    <th className="p-2">Instructions</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRx.items.map((it, i) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="p-2">{i + 1}</td>
                      <td className="p-2 font-bold text-slate-900">
                        {it.medicine_name}
                        {it.generic_name && <span className="block text-[10px] font-normal text-slate-500">({it.generic_name})</span>}
                      </td>
                      <td className="p-2">{it.dosage}</td>
                      <td className="p-2 font-medium text-teal-700">{it.frequency}</td>
                      <td className="p-2">{it.duration}</td>
                      <td className="p-2 text-slate-600">{it.instructions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Advice */}
            {selectedRx.general_advice && (
              <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <p className="font-bold text-slate-700">Advice & Precautions:</p>
                <p className="text-slate-600">{selectedRx.general_advice}</p>
              </div>
            )}

            {/* Signature Block */}
            <div className="pt-6 border-t border-slate-200 flex justify-between items-end">
              <div className="flex items-center gap-1.5 text-emerald-700 text-[11px]">
                <ShieldCheck className="w-4 h-4" />
                <span>Digitally Verified & Issued via ClinicCare SaaS</span>
              </div>
              <div className="text-center">
                <p className="font-bold text-slate-900 border-t border-slate-400 pt-1 min-w-[140px]">
                  {selectedRx.doctor_name}
                </p>
                <p className="text-[10px] text-slate-500">Physician Digital Signature</p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Printer className="w-4 h-4" />}
                onClick={() => window.print()}
              >
                Print Rx
              </Button>
              <Button size="sm" onClick={() => setSelectedRx(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
