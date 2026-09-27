import api from './api'
import { ApiResponse, Feedback } from '@/types'

export interface CreateFeedbackPayload {
  appointment_id?: string
  rating: number
  comment?: string
}

export const feedbackService = {
  createFeedback: async (payload: CreateFeedbackPayload): Promise<Feedback> => {
    const res = await api.post<ApiResponse<Feedback>>('/feedback', payload)
    return res.data.data
  },

  getMyFeedback: async (): Promise<Feedback[]> => {
    const res = await api.get<ApiResponse<Feedback[]>>('/feedback/my')
    return res.data.data
  },
}
