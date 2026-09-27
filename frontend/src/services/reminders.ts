import { api } from './api'
import { FollowUpReminder, ApiResponse } from '@/types'

export const remindersApi = {
  getReminders: async (params?: {
    patient_id?: string
    status?: string
  }): Promise<ApiResponse<FollowUpReminder[]>> => {
    const response = await api.get('/reminders', { params })
    return response.data
  },

  createReminder: async (data: {
    patient_id: string
    appointment_id?: string
    doctor_id?: string
    reminder_type?: string
    scheduled_for: string
    title: string
    message: string
    channel?: string
  }): Promise<ApiResponse<FollowUpReminder>> => {
    const response = await api.post('/reminders', data)
    return response.data
  },

  dispatchReminder: async (id: string): Promise<ApiResponse<FollowUpReminder>> => {
    const response = await api.post(`/reminders/${id}/dispatch`)
    return response.data
  },
}
