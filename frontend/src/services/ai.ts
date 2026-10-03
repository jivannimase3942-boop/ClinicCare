import api from './api'
import { ApiResponse, AIChatResponse, AIConversation } from '@/types'

export interface AIChatPayload {
  message: string
  conversation_id?: string
  language?: string
}

export const aiService = {
  sendMessage: async (payload: AIChatPayload): Promise<AIChatResponse> => {
    const res = await api.post<ApiResponse<AIChatResponse>>('/ai/chat', payload)
    return res.data.data
  },

  getMyConversations: async (): Promise<AIConversation[]> => {
    const res = await api.get<ApiResponse<AIConversation[]>>('/ai/conversations')
    return res.data.data
  },

  getConversationById: async (id: string): Promise<AIConversation> => {
    const res = await api.get<ApiResponse<AIConversation>>(`/ai/conversations/${id}`)
    return res.data.data
  },

  draftClinicalNote: async (patientId: string, rawNotes: string): Promise<any> => {
    const res = await api.post<ApiResponse<any>>('/ai/clinical/draft-note', {
      patient_id: patientId,
      raw_notes: rawNotes,
    })
    return res.data.data
  },

  summarizeLabReport: async (orderId: string): Promise<any> => {
    const res = await api.post<ApiResponse<any>>('/ai/clinical/summarize-report', {
      order_id: orderId,
    })
    return res.data.data
  },
}
