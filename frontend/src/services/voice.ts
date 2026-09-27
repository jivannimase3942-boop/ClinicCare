import api from './api'
import { ApiResponse, VoiceCallRequest } from '@/types'

export interface RequestVoiceCallPayload {
  phone?: string
  reason: string
}

export const voiceService = {
  requestCall: async (payload: RequestVoiceCallPayload): Promise<VoiceCallRequest> => {
    const res = await api.post<ApiResponse<VoiceCallRequest>>('/voice/request', payload)
    return res.data.data
  },

  getMyVoiceRequests: async (): Promise<VoiceCallRequest[]> => {
    const res = await api.get<ApiResponse<VoiceCallRequest[]>>('/voice/my')
    return res.data.data
  },
}
