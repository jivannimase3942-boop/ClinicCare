import api from '@/services/api'
import {
  ApiResponse,
  VitalSign,
  ConsultationRecord,
  ClinicalDocument,
  PatientTimeline,
} from '@/types'

export interface CreateVitalPayload {
  patient_id: string
  appointment_id?: string
  consultation_id?: string
  temperature_celsius?: number
  pulse_bpm?: number
  bp_systolic?: number
  bp_diastolic?: number
  respiratory_rate?: number
  spo2_percent?: number
  weight_kg?: number
  height_cm?: number
  notes?: string
}

export interface CreateConsultationPayload {
  patient_id: string
  appointment_id?: string
  chief_complaint: string
  history_of_present_illness?: string
  medical_history?: string
  allergies?: string
  lifestyle_notes?: string
  examination_notes?: string
  diagnosis: string
  treatment_plan?: string
  investigations_ordered?: string
  follow_up_date?: string
  referral?: string
  clinical_notes?: string
  vitals?: CreateVitalPayload
}

export interface UpdateConsultationPayload {
  chief_complaint?: string
  history_of_present_illness?: string
  medical_history?: string
  allergies?: string
  lifestyle_notes?: string
  examination_notes?: string
  diagnosis?: string
  treatment_plan?: string
  investigations_ordered?: string
  follow_up_date?: string
  referral?: string
  clinical_notes?: string
}

export const clinicalService = {
  recordVitals: async (payload: CreateVitalPayload): Promise<VitalSign> => {
    const res = await api.post<ApiResponse<VitalSign>>('/clinical/vitals', payload)
    return res.data.data
  },

  getPatientVitals: async (patientId: string): Promise<VitalSign[]> => {
    const res = await api.get<ApiResponse<VitalSign[]>>(`/clinical/patients/${patientId}/vitals`)
    return res.data.data
  },

  createConsultation: async (payload: CreateConsultationPayload): Promise<ConsultationRecord> => {
    const res = await api.post<ApiResponse<ConsultationRecord>>('/clinical/consultations', payload)
    return res.data.data
  },

  updateConsultation: async (id: string, payload: UpdateConsultationPayload): Promise<ConsultationRecord> => {
    const res = await api.patch<ApiResponse<ConsultationRecord>>(`/clinical/consultations/${id}`, payload)
    return res.data.data
  },

  finalizeConsultation: async (id: string): Promise<ConsultationRecord> => {
    const res = await api.post<ApiResponse<ConsultationRecord>>(`/clinical/consultations/${id}/finalize`)
    return res.data.data
  },

  getConsultation: async (id: string): Promise<ConsultationRecord> => {
    const res = await api.get<ApiResponse<ConsultationRecord>>(`/clinical/consultations/${id}`)
    return res.data.data
  },

  listPatientConsultations: async (patientId: string, finalizedOnly = false): Promise<ConsultationRecord[]> => {
    const res = await api.get<ApiResponse<ConsultationRecord[]>>(`/clinical/patients/${patientId}/consultations`, {
      params: { finalized_only: finalizedOnly },
    })
    return res.data.data
  },

  getPatientTimeline: async (patientId: string): Promise<PatientTimeline> => {
    const res = await api.get<ApiResponse<PatientTimeline>>(`/clinical/patients/${patientId}/timeline`)
    return res.data.data
  },
}
