import api from './api'
import { ApiResponse, Escalation, EscalationReason, EscalationPriority } from '@/types'

export interface CreateEscalationPayload {
  reason: EscalationReason
  message: string
  priority?: EscalationPriority
}

export const escalationService = {
  createEscalation: async (payload: CreateEscalationPayload): Promise<Escalation> => {
    const res = await api.post<ApiResponse<Escalation>>('/escalations', payload)
    return res.data.data
  },

  getMyEscalations: async (): Promise<Escalation[]> => {
    const res = await api.get<ApiResponse<Escalation[]>>('/escalations/my')
    return res.data.data
  },
}
