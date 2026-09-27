import api from './api'
import { ApiResponse, Appointment } from '@/types'

export interface CreateAppointmentPayload {
  doctor_id: string
  appointment_date: string
  appointment_time: string
  reason?: string
}

export interface RescheduleAppointmentPayload {
  new_date: string
  new_time: string
  reason?: string
}

export interface CancelAppointmentPayload {
  cancellation_reason?: string
}

export const appointmentService = {
  createAppointment: async (payload: CreateAppointmentPayload): Promise<Appointment> => {
    const res = await api.post<ApiResponse<Appointment>>('/appointments', payload)
    return res.data.data
  },

  getMyAppointments: async (status?: string): Promise<Appointment[]> => {
    const res = await api.get<ApiResponse<Appointment[]>>('/appointments/my', {
      params: { status },
    })
    return res.data.data
  },

  getAppointmentById: async (id: string): Promise<Appointment> => {
    const res = await api.get<ApiResponse<Appointment>>(`/appointments/${id}`)
    return res.data.data
  },

  rescheduleAppointment: async (
    id: string,
    payload: RescheduleAppointmentPayload
  ): Promise<Appointment> => {
    const res = await api.patch<ApiResponse<Appointment>>(`/appointments/${id}/reschedule`, payload)
    return res.data.data
  },

  cancelAppointment: async (
    id: string,
    payload?: CancelAppointmentPayload
  ): Promise<Appointment> => {
    const res = await api.patch<ApiResponse<Appointment>>(`/appointments/${id}/cancel`, payload || {})
    return res.data.data
  },
}
