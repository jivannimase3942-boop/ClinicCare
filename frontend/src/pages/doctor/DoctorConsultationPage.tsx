import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clinicalService, CreateConsultationPayload } from '@/services/clinical'
import { doctorPortalService } from '@/services/doctor_portal'
import { useToast } from '@/context/ToastContext'
import { Card, CardTitle, CardHeader, CardDescription } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Stethoscope,
  Activity,
  FileCheck2,
  Save,
  CheckCircle2,
  Clock,
  User,
  History,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react'

export const DoctorConsultationPage: React.FC = () => {
  const { appointmentId } = useParams<{ appointmentId?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [activeConsultationId, setActiveConsultationId] = useState<string | null>(null)
  const [selectedPatientId, setSelectedPatientId] = useState<string>('')
  const [chiefComplaint, setChiefComplaint] = useState('')
  const [historyOfIllness, setHistoryOfIllness] = useState('')
  const [medicalHistory, setMedicalHistory] = useState('')
  const [allergies, setAllergies] = useState('')
  const [examinationNotes, setExaminationNotes] = useState('')
  const [diagnosis, setDiagnosis] = useState('')
  const [treatmentPlan, setTreatmentPlan] = useState('')
  const [followUpDate, setFollowUpDate] = useState('')
  const [clinicalNotes, setClinicalNotes] = useState('')

  // Vitals State
  const [tempCelsius, setTempCelsius] = useState<string>('')
  const [pulse, setPulse] = useState<string>('')
  const [bpSystolic, setBpSystolic] = useState<string>('')
  const [bpDiastolic, setBpDiastolic] = useState<string>('')
  const [respiratoryRate, setRespiratoryRate] = useState<string>('')
  const [spo2, setSpo2] = useState<string>('')
  const [weightKg, setWeightKg] = useState<string>('')
  const [heightCm, setHeightCm] = useState<string>('')
  const [isFinalized, setIsFinalized] = useState(false)

  // Fetch doctor's appointments to link context
  const { data: appointments = [] } = useQuery({
    queryKey: ['doctor-appointments'],
    queryFn: () => doctorPortalService.getAppointments(),
  })

  // Match current appointment if passed
  useEffect(() => {
    if (appointmentId && appointments.length > 0) {
      const match = appointments.find((a) => a.id === appointmentId)
      if (match) {
        setSelectedPatientId(match.patient_id)
        if (match.reason && !chiefComplaint) {
          setChiefComplaint(match.reason)
        }
      }
    }
  }, [appointmentId, appointments])

  // Fetch previous consultations for patient timeline context
  const { data: previousConsultations = [] } = useQuery({
    queryKey: ['patient-consultations', selectedPatientId],
    queryFn: () => clinicalService.listPatientConsultations(selectedPatientId),
    enabled: !!selectedPatientId,
  })

  // Computed BMI
  const calculatedBmi = () => {
    const w = parseFloat(weightKg)
    const h = parseFloat(heightCm)
    if (w > 0 && h > 0) {
      const hm = h / 100
      return (w / (hm * hm)).toFixed(1)
    }
    return null
  }

  // Create or Update Draft Mutation
  const saveDraftMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPatientId || !chiefComplaint || !diagnosis) {
        throw new Error('Patient, chief complaint, and diagnosis are required.')
      }

      const vitalsPayload = (tempCelsius || pulse || bpSystolic || spo2 || weightKg) ? {
        patient_id: selectedPatientId,
        appointment_id: appointmentId || undefined,
        temperature_celsius: tempCelsius ? parseFloat(tempCelsius) : undefined,
        pulse_bpm: pulse ? parseInt(pulse) : undefined,
        bp_systolic: bpSystolic ? parseInt(bpSystolic) : undefined,
        bp_diastolic: bpDiastolic ? parseInt(bpDiastolic) : undefined,
        respiratory_rate: respiratoryRate ? parseInt(respiratoryRate) : undefined,
        spo2_percent: spo2 ? parseFloat(spo2) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
      } : undefined

      if (activeConsultationId) {
        return clinicalService.updateConsultation(activeConsultationId, {
          chief_complaint: chiefComplaint,
          history_of_present_illness: historyOfIllness,
          medical_history: medicalHistory,
          allergies: allergies,
          examination_notes: examinationNotes,
          diagnosis: diagnosis,
          treatment_plan: treatmentPlan,
          follow_up_date: followUpDate || undefined,
          clinical_notes: clinicalNotes,
        })
      } else {
        return clinicalService.createConsultation({
          patient_id: selectedPatientId,
          appointment_id: appointmentId || undefined,
          chief_complaint: chiefComplaint,
          history_of_present_illness: historyOfIllness,
          medical_history: medicalHistory,
          allergies: allergies,
          examination_notes: examinationNotes,
          diagnosis: diagnosis,
          treatment_plan: treatmentPlan,
          follow_up_date: followUpDate || undefined,
          clinical_notes: clinicalNotes,
          vitals: vitalsPayload,
        })
      }
    },
    onSuccess: (data) => {
      setActiveConsultationId(data.id)
      showToast('Consultation draft saved successfully', 'success')
      queryClient.invalidateQueries({ queryKey: ['patient-consultations', selectedPatientId] })
    },
    onError: (err: any) => showToast(err.message || 'Failed to save draft', 'error'),
  })

  // Finalize Mutation
  const finalizeMutation = useMutation({
    mutationFn: async () => {
      let id = activeConsultationId
      if (!id) {
        // Save first
        const saved = await saveDraftMutation.mutateAsync()
        id = saved.id
      }
      return clinicalService.finalizeConsultation(id)
    },
    onSuccess: (data) => {
      setIsFinalized(true)
      showToast('Clinical consultation finalized and encounter completed!', 'success')
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] })
      queryClient.invalidateQueries({ queryKey: ['patient-consultations', selectedPatientId] })
    },
    onError: (err: any) => showToast(err.message || 'Failed to finalize consultation', 'error'),
  })

  const currentAppointment = appointments.find((a) => a.id === appointmentId)

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/doctor/appointments')}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back to OPD Queue
          </button>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-teal-600" />
            Clinical Consultation Workspace
          </h1>
          <p className="text-xs text-slate-500">
            Longitudinal patient encounter, clinical examination, vitals, and structured diagnosis
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isFinalized ? (
            <Badge variant="success" className="px-3 py-1 text-xs">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> FINALIZED RECORD
            </Badge>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Save className="w-4 h-4" />}
                onClick={() => saveDraftMutation.mutate()}
                isLoading={saveDraftMutation.isPending}
              >
                Save Draft
              </Button>
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
                leftIcon={<FileCheck2 className="w-4 h-4" />}
                onClick={() => finalizeMutation.mutate()}
                isLoading={finalizeMutation.isPending}
              >
                Finalize Record
              </Button>
            </>
          )}
        </div>
      </div>

      {isFinalized && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3 text-xs text-emerald-800">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div>
            <p className="font-bold">This clinical consultation has been finalized.</p>
            <p className="text-emerald-700">
              The medical record is now locked for regulatory integrity and version audit.
            </p>
          </div>
        </div>
      )}

      {/* Patient Header Banner */}
      <Card className="bg-gradient-to-r from-teal-50 to-sky-50 border border-teal-100 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 text-base">
                {currentAppointment ? currentAppointment.patient_name : 'Patient Consultation'}
              </h2>
              <p className="text-xs text-slate-600">
                {currentAppointment ? `Token #${currentAppointment.token_number || 'N/A'} • ${currentAppointment.appointment_time}` : 'Direct Clinical Encounter'}
              </p>
            </div>
          </div>
          {currentAppointment && (
            <Badge variant="primary" className="self-start sm:self-center">
              {currentAppointment.appointment_type || 'OPD Consultation'}
            </Badge>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Clinical Note Section (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="space-y-4">
            <CardTitle className="text-sm flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-teal-600" /> 1. Chief Complaint & History
            </CardTitle>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 mb-1 block">Chief Complaint *</label>
                <Input
                  disabled={isFinalized}
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  placeholder="e.g. High fever for 2 days, dry persistent cough"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 mb-1 block">History of Present Illness (HPI)</label>
                <textarea
                  disabled={isFinalized}
                  value={historyOfIllness}
                  onChange={(e) => setHistoryOfIllness(e.target.value)}
                  placeholder="Onset, duration, severity, aggravating/relieving factors..."
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-slate-100"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 mb-1 block">Medical / Surgical History</label>
                  <Input
                    disabled={isFinalized}
                    value={medicalHistory}
                    onChange={(e) => setMedicalHistory(e.target.value)}
                    placeholder="e.g. Hypertension (5 yrs), appendectomy (2018)"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 mb-1 block">Known Allergies</label>
                  <Input
                    disabled={isFinalized}
                    value={allergies}
                    onChange={(e) => setAllergies(e.target.value)}
                    placeholder="e.g. Penicillin, Sulfa drugs, NKDA"
                  />
                </div>
              </div>
            </div>
          </Card>

          <Card className="space-y-4">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-600" /> 2. Clinical Examination & Diagnosis
            </CardTitle>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 mb-1 block">Physical Examination Notes</label>
                <textarea
                  disabled={isFinalized}
                  value={examinationNotes}
                  onChange={(e) => setExaminationNotes(e.target.value)}
                  placeholder="General condition, chest, CVS, abdomen, ENT examination findings..."
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:bg-slate-100"
                  rows={3}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 mb-1 block">Diagnosis / Clinical Impression *</label>
                <Input
                  disabled={isFinalized}
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="Primary clinical diagnosis (e.g. Acute Bronchitis, Type 2 Diabetes)"
                  required
                />
              </div>
            </div>
          </Card>

          <Card className="space-y-4">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-emerald-600" /> 3. Treatment Plan & Follow-Up
            </CardTitle>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 mb-1 block">Treatment & Management Plan</label>
                <textarea
                  disabled={isFinalized}
                  value={treatmentPlan}
                  onChange={(e) => setTreatmentPlan(e.target.value)}
                  placeholder="Medication regimen, dosage instructions, diet/lifestyle modifications..."
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:bg-slate-100"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-700 mb-1 block">Recommended Follow-up Date</label>
                  <Input
                    type="date"
                    disabled={isFinalized}
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 mb-1 block">Confidential Clinical Notes</label>
                  <Input
                    disabled={isFinalized}
                    value={clinicalNotes}
                    onChange={(e) => setClinicalNotes(e.target.value)}
                    placeholder="Internal physician remarks..."
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar: Vitals & History (1 Col) */}
        <div className="space-y-6">
          {/* Vitals Recording Widget */}
          <Card className="space-y-4">
            <CardHeader className="p-0">
              <CardTitle className="text-sm flex items-center gap-2">
                <Activity className="w-4 h-4 text-rose-500" /> Patient Vitals
              </CardTitle>
              {calculatedBmi() && (
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                  BMI: {calculatedBmi()} kg/m²
                </span>
              )}
            </CardHeader>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">BP (Systolic)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="120"
                  value={bpSystolic}
                  onChange={(e) => setBpSystolic(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">BP (Diastolic)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="80"
                  value={bpDiastolic}
                  onChange={(e) => setBpDiastolic(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">Pulse (bpm)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="72"
                  value={pulse}
                  onChange={(e) => setPulse(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">SpO2 (%)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="98"
                  value={spo2}
                  onChange={(e) => setSpo2(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">Temp (°C)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  step="0.1"
                  placeholder="37.0"
                  value={tempCelsius}
                  onChange={(e) => setTempCelsius(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">Resp Rate</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="16"
                  value={respiratoryRate}
                  onChange={(e) => setRespiratoryRate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">Weight (kg)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  step="0.5"
                  placeholder="70"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-500 font-semibold">Height (cm)</label>
                <Input
                  disabled={isFinalized}
                  type="number"
                  placeholder="175"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                />
              </div>
            </div>
          </Card>

          {/* Previous Medical History */}
          <Card className="space-y-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" /> Prior Consultations ({previousConsultations.length})
            </CardTitle>
            {previousConsultations.length === 0 ? (
              <p className="text-xs text-slate-400 py-3 text-center">No prior consultation records on file.</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {previousConsultations.map((c) => (
                  <div key={c.id} className="p-2.5 bg-slate-50 border rounded-xl text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-800">{c.diagnosis}</span>
                      <Badge variant={c.is_finalized ? 'success' : 'default'} className="text-[10px]">
                        {c.status}
                      </Badge>
                    </div>
                    <p className="text-slate-500 text-[11px]">{new Date(c.created_at).toLocaleDateString()}</p>
                    {c.treatment_plan && (
                      <p className="text-slate-600 text-[11px] truncate">Rx: {c.treatment_plan}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
