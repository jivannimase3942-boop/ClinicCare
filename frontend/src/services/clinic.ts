import api from './api'
import { ApiResponse, Clinic, AuditLog } from '@/types'

export interface ClinicOnboardPayload {
  name: string
  slug?: string
  phone?: string
  email?: string
  address?: string
  city?: string
  state?: string
  pincode?: string
  country?: string
  operating_hours?: string
  consultation_fee_default?: number
  departments?: string[]
  services?: string[]
  admin_name: string
  admin_email: string
  admin_password: string
  admin_phone?: string
  doctor_name?: string
  doctor_email?: string
  doctor_specialization?: string
  doctor_qualification?: string
  doctor_fee?: number
}

export interface ClinicOnboardResult {
  clinic: Clinic
  admin_user: {
    id: string
    email: string
    full_name: string
    role: string
    clinic_id: string
  }
  doctor_user?: {
    id: string
    email: string
    full_name: string
    role: string
    specialization?: string
  } | null
  portal_url: string
  message: string
}

export interface PublicClinicProfile {
  id: string
  name: string
  slug: string
  phone?: string | null
  email?: string | null
  address?: string | null
  city?: string | null
  state?: string | null
  pincode?: string | null
  country?: string | null
  operating_hours: string
  consultation_fee_default: number
  departments: string[]
}

export const clinicService = {
  onboardClinic: async (payload: ClinicOnboardPayload): Promise<ClinicOnboardResult> => {
    const res = await api.post<ApiResponse<ClinicOnboardResult>>('/clinics/onboard', payload)
    return res.data.data
  },

  getCurrentClinic: async (): Promise<Clinic> => {
    const res = await api.get<ApiResponse<Clinic>>('/clinics/current')
    return res.data.data
  },

  updateCurrentClinic: async (payload: Partial<Clinic>): Promise<Clinic> => {
    const res = await api.patch<ApiResponse<Clinic>>('/clinics/current', payload)
    return res.data.data
  },

  getPublicClinic: async (slug: string): Promise<PublicClinicProfile> => {
    const res = await api.get<ApiResponse<PublicClinicProfile>>(`/clinics/public/${slug}`)
    return res.data.data
  },

  listClinics: async (): Promise<Clinic[]> => {
    const res = await api.get<ApiResponse<Clinic[]>>('/clinics')
    return res.data.data
  },

  getAuditLogs: async (params?: { action?: string; limit?: number; offset?: number }): Promise<AuditLog[]> => {
    const res = await api.get<ApiResponse<AuditLog[]>>('/admin/audit-logs', { params })
    return res.data.data
  },
}
