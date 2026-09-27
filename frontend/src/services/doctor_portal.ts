import api from './api'
import { ApiResponse, Appointment } from '@/types'

export const doctorPortalService = {
  getAppointments: async (params?: { date?: string; status?: string }): Promise<Appointment[]> => {
    const res = await api.get<ApiResponse<Appointment[]>>('/doctor/appointments', { params })
    return res.data.data
  },

  updateAppointmentStatus: async (
    id: string,
    status: string,
    notes?: string
  ): Promise<Appointment> => {
    const res = await api.patch<ApiResponse<Appointment>>(`/doctor/appointments/${id}/status`, {
      status,
      notes,
    })
    return res.data.data
  },
}
