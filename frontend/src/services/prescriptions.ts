import api from '@/services/api'
import {
  ApiResponse,
  Medicine,
  Prescription,
  PrescriptionItem,
} from '@/types'

export interface CreatePrescriptionPayload {
  patient_id: string
  appointment_id?: string
  consultation_id?: string
  diagnosis_summary: string
  general_advice?: string
  diet_lifestyle_notes?: string
  follow_up_date?: string
  items: PrescriptionItem[]
}

export interface CreateMedicinePayload {
  brand_name: string
  generic_name: string
  strength: string
  dosage_form: string
  manufacturer?: string
  category: string
  hsn_code?: string
  gst_rate_percent: number
  unit_price: number
}

export const prescriptionService = {
  listMedicines: async (search?: string): Promise<Medicine[]> => {
    const res = await api.get<ApiResponse<Medicine[]>>('/prescriptions/medicines', {
      params: { search },
    })
    return res.data.data
  },

  createMedicine: async (payload: CreateMedicinePayload): Promise<Medicine> => {
    const res = await api.post<ApiResponse<Medicine>>('/prescriptions/medicines', payload)
    return res.data.data
  },

  createPrescription: async (payload: CreatePrescriptionPayload): Promise<Prescription> => {
    const res = await api.post<ApiResponse<Prescription>>('/prescriptions', payload)
    return res.data.data
  },

  finalizePrescription: async (id: string): Promise<Prescription> => {
    const res = await api.post<ApiResponse<Prescription>>(`/prescriptions/${id}/finalize`)
    return res.data.data
  },

  getPrescription: async (id: string): Promise<Prescription> => {
    const res = await api.get<ApiResponse<Prescription>>(`/prescriptions/${id}`)
    return res.data.data
  },

  listPatientPrescriptions: async (patientId: string, finalizedOnly = false): Promise<Prescription[]> => {
    const res = await api.get<ApiResponse<Prescription[]>>(`/prescriptions/patient/${patientId}`, {
      params: { finalized_only: finalizedOnly },
    })
    return res.data.data
  },
}
