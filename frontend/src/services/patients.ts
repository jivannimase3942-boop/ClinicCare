import { api } from './api'
import { PatientProfile, VisitHistory, ApiResponse } from '@/types'

export interface PatientRecord {
  id: string
  user_id: string
  full_name: string
  email: string
  phone?: string | null
  date_of_birth?: string | null
  gender?: string | null
  blood_group?: string | null
  address?: string | null
  emergency_contact?: string | null
  created_at: string
  updated_at: string
}

export const patientsApi = {
  searchPatients: async (params?: {
    search?: string
    blood_group?: string
    gender?: string
  }): Promise<ApiResponse<PatientRecord[]>> => {
    const response = await api.get('/patients', { params })
    return response.data
  },

  getPatient: async (id: string): Promise<ApiResponse<PatientRecord>> => {
    const response = await api.get(`/patients/${id}`)
    return response.data
  },

  updatePatient: async (
    id: string,
    data: Partial<PatientRecord>
  ): Promise<ApiResponse<PatientRecord>> => {
    const response = await api.patch(`/patients/${id}`, data)
    return response.data
  },

  getPatientVisits: async (patientId: string): Promise<ApiResponse<VisitHistory[]>> => {
    const response = await api.get(`/patients/${patientId}/visits`)
    return response.data
  },

  recordVisit: async (
    patientId: string,
    data: Partial<VisitHistory>
  ): Promise<ApiResponse<VisitHistory>> => {
    const response = await api.post(`/patients/${patientId}/visits`, data)
    return response.data
  },
}
