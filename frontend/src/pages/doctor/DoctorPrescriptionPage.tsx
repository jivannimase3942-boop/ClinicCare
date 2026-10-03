import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { prescriptionService } from '@/services/prescriptions'
import { doctorPortalService } from '@/services/doctor_portal'
import { Prescription, PrescriptionItem, Medicine } from '@/types'
import { useToast } from '@/context/ToastContext'
import { Card, CardTitle, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import {
  Pill,
  Plus,
  Trash2,
  FileCheck2,
  Printer,
  Search,
  CheckCircle2,
  ArrowLeft,
  Calendar,
  User,
  ShieldCheck,
} from 'lucide-react'

export const DoctorPrescriptionPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const initialPatientId = searchParams.get('patient_id') || ''
  const initialAppointmentId = searchParams.get('appointment_id') || ''
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [selectedPatientId, setSelectedPatientId] = useState(initialPatientId)
  const [diagnosisSummary, setDiagnosisSummary] = useState('')
  const [generalAdvice, setGeneralAdvice] = useState('Drink adequate water, maintain rest, and take medications as advised.')
  const [lifestyleNotes, setLifestyleNotes] = useState('')
  const [followUpDate, setFollowUpDate] = useState('')
  const [medSearch, setMedSearch] = useState('')

  // Medicine items list
  const [items, setItems] = useState<PrescriptionItem[]>([
    {
      medicine_name: 'Paracetamol 650mg',
      generic_name: 'Paracetamol',
      dosage_form: 'TABLET',
      strength: '650 mg',
      dosage: '1 tablet',
      frequency: '1-0-1 (Twice daily)',
      duration: '5 days',
      route: 'ORAL',
      instructions: 'After meals',
      quantity: 10,
    },
  ])

  // Printable Rx Preview modal
  const [previewPrescription, setPreviewPrescription] = useState<Prescription | null>(null)

  // Fetch doctor appointments to populate active patient dropdown
  const { data: appointments = [] } = useQuery({
    queryKey: ['doctor-appointments'],
    queryFn: () => doctorPortalService.getAppointments(),
  })

  // Fetch medicines formulary master
  const { data: formulary = [] } = useQuery({
    queryKey: ['formulary-medicines', medSearch],
    queryFn: () => prescriptionService.listMedicines(medSearch || undefined),
  })

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      {
        medicine_name: '',
        generic_name: '',
        dosage_form: 'TABLET',
        strength: '',
        dosage: '1 tablet',
        frequency: '1-0-1 (Twice daily)',
        duration: '5 days',
        route: 'ORAL',
        instructions: 'After meals',
        quantity: 10,
      },
    ])
  }

  const removeItem = (idx: number) => {
    setItems((prev) => prev.filter((_, i) => i !== idx))
  }

  const updateItem = (idx: number, field: keyof PrescriptionItem, val: any) => {
    setItems((prev) => {
      const copy = [...prev]
      copy[idx] = { ...copy[idx], [field]: val }
      return copy
    })
  }

  const selectFormularyMed = (idx: number, med: Medicine) => {
    setItems((prev) => {
      const copy = [...prev]
      copy[idx] = {
        ...copy[idx],
        medicine_id: med.id,
        medicine_name: med.brand_name,
        generic_name: med.generic_name,
        dosage_form: med.dosage_form,
        strength: med.strength,
      }
      return copy
    })
  }

  // Create and Finalize Mutation
  const issueMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPatientId || !diagnosisSummary) {
        throw new Error('Please select a patient and provide a diagnosis summary.')
      }
      if (items.length === 0 || !items[0].medicine_name) {
        throw new Error('Please add at least one medication.')
      }

      // Step 1: Create draft
      const draft = await prescriptionService.createPrescription({
        patient_id: selectedPatientId,
        appointment_id: initialAppointmentId || undefined,
        diagnosis_summary: diagnosisSummary,
        general_advice: generalAdvice,
        diet_lifestyle_notes: lifestyleNotes,
        follow_up_date: followUpDate || undefined,
        items,
      })

      // Step 2: Finalize & issue
      const finalized = await prescriptionService.finalizePrescription(draft.id)
      return finalized
    },
    onSuccess: (data) => {
      showToast(`Digital Prescription ${data.prescription_number} signed & issued!`, 'success')
      setPreviewPrescription(data)
      queryClient.invalidateQueries({ queryKey: ['patient-prescriptions'] })
    },
    onError: (err: any) => showToast(err.message || 'Prescription issuance failed', 'error'),
  })

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/doctor/appointments')}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Consultations
          </button>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-teal-600" />
            Digital Prescription Writer
          </h1>
          <p className="text-xs text-slate-500">
            Formulary-linked electronic prescription with human physician verification & signature
          </p>
        </div>

        <Button
          size="sm"
          className="bg-teal-600 hover:bg-teal-700 text-white"
          leftIcon={<FileCheck2 className="w-4 h-4" />}
          onClick={() => issueMutation.mutate()}
          isLoading={issueMutation.isPending}
        >
          Sign & Issue Prescription
        </Button>
      </div>

      {/* Patient & Encounter Picker */}
      <Card className="p-4 space-y-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <User className="w-4 h-4 text-teal-600" /> 1. Patient & Encounter Details
        </CardTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block">Patient *</label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
              required
            >
              <option value="">Select active consultation patient...</option>
              {appointments.map((a) => (
                <option key={a.id} value={a.patient_id}>
                  {a.patient_name} (Token #{a.token_number || 'N/A'} - {a.appointment_time})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block">Diagnosis Summary *</label>
            <Input
              value={diagnosisSummary}
              onChange={(e) => setDiagnosisSummary(e.target.value)}
              placeholder="e.g. Acute Pharyngitis, Essential Hypertension"
              required
            />
          </div>
        </div>
      </Card>

      {/* Medication Items */}
      <Card className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Pill className="w-4 h-4 text-indigo-600" /> 2. Prescribed Medications ({items.length})
          </CardTitle>
          <Button size="sm" variant="outline" leftIcon={<Plus className="w-3.5 h-3.5" />} onClick={addItem}>
            Add Medicine
          </Button>
        </div>

        <div className="space-y-4">
          {items.map((item, idx) => (
            <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-xs font-bold text-slate-800">Medication #{idx + 1}</span>
                {items.length > 1 && (
                  <button
                    onClick={() => removeItem(idx)}
                    className="text-red-500 hover:text-red-700 text-xs flex items-center gap-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Remove
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Medicine Brand Name *</label>
                  <Input
                    value={item.medicine_name}
                    onChange={(e) => updateItem(idx, 'medicine_name', e.target.value)}
                    placeholder="e.g. Amoxyclav 625"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Generic Composition</label>
                  <Input
                    value={item.generic_name || ''}
                    onChange={(e) => updateItem(idx, 'generic_name', e.target.value)}
                    placeholder="e.g. Amoxicillin + Clavulanate"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Dosage Form</label>
                  <select
                    value={item.dosage_form}
                    onChange={(e) => updateItem(idx, 'dosage_form', e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200"
                  >
                    <option value="TABLET">Tablet</option>
                    <option value="CAPSULE">Capsule</option>
                    <option value="SYRUP">Syrup</option>
                    <option value="INJECTION">Injection</option>
                    <option value="DROPS">Drops</option>
                    <option value="OINTMENT">Ointment / Gel</option>
                    <option value="INHALER">Inhaler</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Dosage</label>
                  <Input
                    value={item.dosage}
                    onChange={(e) => updateItem(idx, 'dosage', e.target.value)}
                    placeholder="1 tablet"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Frequency</label>
                  <select
                    value={item.frequency}
                    onChange={(e) => updateItem(idx, 'frequency', e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200"
                  >
                    <option value="1-0-1 (Twice daily)">1-0-1 (Twice daily)</option>
                    <option value="1-0-0 (Morning)">1-0-0 (Morning)</option>
                    <option value="0-0-1 (Night)">0-0-1 (Night)</option>
                    <option value="1-1-1 (Thrice daily)">1-1-1 (Thrice daily)</option>
                    <option value="SOS (As needed)">SOS (As needed)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Duration</label>
                  <Input
                    value={item.duration}
                    onChange={(e) => updateItem(idx, 'duration', e.target.value)}
                    placeholder="5 days"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-600">Instructions</label>
                  <select
                    value={item.instructions}
                    onChange={(e) => updateItem(idx, 'instructions', e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200"
                  >
                    <option value="After meals">After meals</option>
                    <option value="Before meals">Before meals</option>
                    <option value="Empty stomach">Empty stomach</option>
                    <option value="At bedtime">At bedtime</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Advice & Follow-Up */}
      <Card className="p-4 space-y-4">
        <CardTitle className="text-sm">3. General Advice & Follow-up Instructions</CardTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block">General Medical Advice</label>
            <textarea
              value={generalAdvice}
              onChange={(e) => setGeneralAdvice(e.target.value)}
              className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none"
              rows={2}
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 mb-1 block">Diet & Lifestyle Precautions</label>
            <textarea
              value={lifestyleNotes}
              onChange={(e) => setLifestyleNotes(e.target.value)}
              placeholder="e.g. Low sodium diet, avoid strenuous exercise..."
              className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none"
              rows={2}
            />
          </div>
        </div>
        <div className="max-w-xs">
          <label className="text-xs font-bold text-slate-700 mb-1 block">Follow-up Date</label>
          <Input
            type="date"
            value={followUpDate}
            onChange={(e) => setFollowUpDate(e.target.value)}
          />
        </div>
      </Card>

      {/* Printable Preview Modal */}
      {previewPrescription && (
        <Modal
          isOpen={!!previewPrescription}
          onClose={() => setPreviewPrescription(null)}
          title={`Digital Prescription — ${previewPrescription.prescription_number}`}
        >
          <div className="space-y-6 p-2 text-xs">
            {/* Clinic & Doctor Header */}
            <div className="border-b-2 border-teal-600 pb-4 flex justify-between items-start">
              <div>
                <h2 className="text-lg font-black text-slate-900">{previewPrescription.clinic_name || 'ClinicCare Central'}</h2>
                <p className="text-slate-500">{previewPrescription.clinic_address || 'Healthcare Boulevard'}</p>
                <p className="text-slate-500">Phone: {previewPrescription.clinic_phone || '+91 80 2345 6789'}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-slate-900 text-sm">{previewPrescription.doctor_name}</p>
                <p className="text-slate-600">{previewPrescription.doctor_specialization}</p>
                <p className="text-slate-400">{previewPrescription.doctor_qualification || 'MBBS, MD'}</p>
              </div>
            </div>

            {/* Patient Header */}
            <div className="bg-slate-50 p-3 rounded-xl border flex justify-between">
              <div>
                <p className="font-bold text-slate-800">Patient: {previewPrescription.patient_name}</p>
                <p className="text-slate-500">Phone: {previewPrescription.patient_phone || 'N/A'}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-teal-800">Rx No: {previewPrescription.prescription_number}</p>
                <p className="text-slate-500">Date: {new Date(previewPrescription.created_at).toLocaleDateString()}</p>
              </div>
            </div>

            {/* Diagnosis */}
            <div>
              <span className="font-bold text-slate-700">Diagnosis: </span>
              <span className="text-slate-900 font-semibold">{previewPrescription.diagnosis_summary}</span>
            </div>

            {/* Medication Table */}
            <div>
              <h4 className="font-black text-base text-slate-900 mb-2 font-serif">℞ Prescription</h4>
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
                  {previewPrescription.items.map((it, i) => (
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

            {/* Advice & Follow-up */}
            {previewPrescription.general_advice && (
              <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <p className="font-bold text-slate-700">Advice:</p>
                <p className="text-slate-600">{previewPrescription.general_advice}</p>
              </div>
            )}

            {/* Doctor Signature Block */}
            <div className="pt-6 border-t border-slate-200 flex justify-between items-end">
              <div className="flex items-center gap-1.5 text-emerald-700 text-[11px]">
                <ShieldCheck className="w-4 h-4" />
                <span>Digitally Verified & Issued via ClinicCare SaaS</span>
              </div>
              <div className="text-center">
                <p className="font-bold text-slate-900 border-t border-slate-400 pt-1 min-w-[140px]">
                  {previewPrescription.doctor_name}
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
              <Button size="sm" onClick={() => setPreviewPrescription(null)}>
                Done
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
