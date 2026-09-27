import { api } from './api'
import { Facility, ApiResponse } from '@/types'

export const facilitiesApi = {
  getFacilities: async (params?: {
    city?: string
    facility_type?: string
    search?: string
  }): Promise<ApiResponse<Facility[]>> => {
    const response = await api.get('/facilities', { params })
    return response.data
  },

  createFacility: async (data: Partial<Facility>): Promise<ApiResponse<Facility>> => {
    const response = await api.post('/facilities', data)
    return response.data
  },
}
