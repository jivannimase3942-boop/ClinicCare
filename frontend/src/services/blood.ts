import { api } from './api'
import { BloodBank, BloodGroupSearchResult, BloodInventoryItem, BloodRequest, ApiResponse } from '@/types'

export const bloodApi = {
  getBanks: async (city?: string): Promise<ApiResponse<BloodBank[]>> => {
    const params = city ? { city } : {}
    const response = await api.get('/blood/banks', { params })
    return response.data
  },

  searchBlood: async (params: {
    blood_group?: string
    city?: string
  }): Promise<ApiResponse<BloodGroupSearchResult[]>> => {
    const response = await api.get('/blood/search', { params })
    return response.data
  },

  updateInventory: async (
    id: string,
    data: { units_available: number; status?: string }
  ): Promise<ApiResponse<BloodInventoryItem>> => {
    const response = await api.patch(`/blood/inventory/${id}`, data)
    return response.data
  },

  createBloodRequest: async (data: {
    patient_name: string
    blood_group: string
    units_required: number
    hospital_clinic_name: string
    location: string
    contact_phone: string
    urgency?: string
    additional_info?: string
    patient_id?: string
  }): Promise<ApiResponse<BloodRequest>> => {
    const response = await api.post('/blood/requests', data)
    return response.data
  },

  getBloodRequests: async (params?: {
    status?: string
    blood_group?: string
    urgency?: string
    patient_id?: string
  }): Promise<ApiResponse<BloodRequest[]>> => {
    const response = await api.get('/blood/requests', { params })
    return response.data
  },

  updateBloodRequestStatus: async (
    id: string,
    data: { status: string; admin_notes?: string; matched_blood_bank_id?: string; matched_bank_name?: string }
  ): Promise<ApiResponse<BloodRequest>> => {
    const response = await api.patch(`/blood/requests/${id}`, data)
    return response.data
  },

  matchBloodBank: async (
    requestId: string,
    bloodBankId: string,
    notes?: string
  ): Promise<ApiResponse<BloodRequest>> => {
    const response = await api.post(`/blood/requests/${requestId}/match`, {
      blood_bank_id: bloodBankId,
      notes,
    })
    return response.data
  },
}

