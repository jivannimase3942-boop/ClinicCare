import api from './api'
import { ApiResponse, Appointment, WaitlistEntry, AppointmentType, QueueStatus } from '@/types'

export interface CreateAppointmentPayload {
  doctor_id: string
  appointment_date: string
  appointment_time: string
  reason?: string
  notes?: string
  patient_id?: string
  patient_name?: string
  patient_phone?: string
  appointment_type?: AppointmentType | string
  is_walk_in?: boolean
  parent_appointment_id?: string
}

export interface WalkInPayload {
  doctor_id: string
  patient_name: string
  patient_phone: string
  patient_email?: string
  reason?: string
  appointment_type?: AppointmentType | string
}

export interface RescheduleAppointmentPayload {
  new_date: string
  new_time: string
  reason?: string
}

export interface CancelAppointmentPayload {
  cancellation_reason?: string
  cancelled_reason?: string
}

export const appointmentService = {
  createAppointment: async (payload: CreateAppointmentPayload): Promise<Appointment> => {
    const res = await api.post<ApiResponse<Appointment>>('/appointments', payload)
    return res.data.data
  },

  createWalkIn: async (payload: WalkInPayload): Promise<Appointment> => {
    const res = await api.post<ApiResponse<Appointment>>('/appointments/walk-in', payload)
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

  checkIn: async (id: string): Promise<Appointment> => {
    const res = await api.post<ApiResponse<Appointment>>(`/appointments/${id}/check-in`)
    return res.data.data
  },

  updateQueue: async (id: string, queue_status: QueueStatus | string, notes?: string): Promise<Appointment> => {
    const res = await api.patch<ApiResponse<Appointment>>(`/appointments/${id}/queue`, { queue_status, notes })
    return res.data.data
  },

  getTodayQueue: async (doctorId?: string): Promise<Appointment[]> => {
    const res = await api.get<ApiResponse<Appointment[]>>('/appointments/queue/today', {
      params: { doctor_id: doctorId },
    })
    return res.data.data
  },

  joinWaitlist: async (payload: { doctor_id: string; desired_date: string; preferred_time_range?: string; notes?: string }): Promise<WaitlistEntry> => {
    const res = await api.post<ApiResponse<WaitlistEntry>>('/appointments/waitlist', payload)
    return res.data.data
  },

  getWaitlist: async (params?: { doctor_id?: string; desired_date?: string }): Promise<WaitlistEntry[]> => {
    const res = await api.get<ApiResponse<WaitlistEntry[]>>('/appointments/waitlist', { params })
    return res.data.data
  },

  convertWaitlist: async (id: string, appointmentTime: string): Promise<Appointment> => {
    const res = await api.post<ApiResponse<Appointment>>(`/appointments/waitlist/${id}/convert?appointment_time=${appointmentTime}`)
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

