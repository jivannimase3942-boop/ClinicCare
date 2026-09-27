import api from './api'
import { ApiResponse, MedicalReport } from '@/types'

export const reportService = {
  getMyReports: async (): Promise<MedicalReport[]> => {
    const res = await api.get<ApiResponse<MedicalReport[]>>('/reports/my')
    return res.data.data
  },
}
