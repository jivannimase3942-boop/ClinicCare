import { api } from './api'
import { Ambulance, AmbulanceRequest, ApiResponse } from '@/types'

export const ambulanceApi = {
  getAmbulances: async (status?: string): Promise<ApiResponse<Ambulance[]>> => {
    const params = status ? { status } : {}
    const response = await api.get('/ambulances', { params })
    return response.data
  },

  requestAmbulance: async (data: {
    requester_name: string
    requester_phone: string
    pickup_address: string
    destination_facility?: string
    emergency_priority?: string
    notes?: string
    patient_id?: string
  }): Promise<ApiResponse<AmbulanceRequest>> => {
    const response = await api.post('/ambulances/request', data)
    return response.data
  },

  getRequests: async (params?: {
    status?: string
    priority?: string
    patient_id?: string
  }): Promise<ApiResponse<AmbulanceRequest[]>> => {
    const response = await api.get('/ambulances/requests', { params })
    return response.data
  },

  updateRequestStatus: async (
    id: string,
    data: { status: string; notes?: string; ambulance_id?: string }
  ): Promise<ApiResponse<AmbulanceRequest>> => {
    const response = await api.patch(`/ambulances/requests/${id}`, data)
    return response.data
  },

  assignAmbulance: async (
    requestId: string,
    ambulanceId: string,
    notes?: string
  ): Promise<ApiResponse<AmbulanceRequest>> => {
    const response = await api.post(`/ambulances/requests/${requestId}/assign`, {
      ambulance_id: ambulanceId,
      notes,
    })
    return response.data
  },

  updateAmbulanceStatus: async (
    id: string,
    data: { status: string; current_location?: string }
  ): Promise<ApiResponse<Ambulance>> => {
    const response = await api.patch(`/ambulances/${id}`, data)
    return response.data
  },
}
