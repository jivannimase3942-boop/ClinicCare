import { api } from './api'
import { EmergencyRequest, EmergencyStats, ApiResponse } from '@/types'

export const emergencyApi = {
  getStats: async (): Promise<ApiResponse<EmergencyStats>> => {
    const response = await api.get('/emergencies/stats')
    return response.data
  },

  createRequest: async (data: {
    caller_name: string
    caller_phone: string
    location: string
    emergency_type: string
    priority?: string
    notes?: string
    requires_ambulance?: boolean
    patient_id?: string
  }): Promise<ApiResponse<EmergencyRequest>> => {
    const response = await api.post('/emergencies', data)
    return response.data
  },

  getEmergencies: async (): Promise<ApiResponse<EmergencyRequest[]>> => {
    const response = await api.get('/emergencies')
    return response.data
  },
}
