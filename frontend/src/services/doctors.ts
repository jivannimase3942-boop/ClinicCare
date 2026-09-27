import api from './api'
import { ApiResponse, Doctor, Department, DoctorSlot } from '@/types'

export const doctorService = {
  getDepartments: async (): Promise<Department[]> => {
    const res = await api.get<ApiResponse<Department[]>>('/departments')
    return res.data.data
  },

  getDoctors: async (params?: { department_id?: string; search?: string }): Promise<Doctor[]> => {
    const res = await api.get<ApiResponse<Doctor[]>>('/doctors', { params })
    return res.data.data
  },

  getDoctorById: async (id: string): Promise<Doctor> => {
    const res = await api.get<ApiResponse<Doctor>>(`/doctors/${id}`)
    return res.data.data
  },

  getDoctorSlots: async (doctorId: string, date: string): Promise<DoctorSlot[]> => {
    const res = await api.get<ApiResponse<DoctorSlot[]>>(`/doctors/${doctorId}/slots`, {
      params: { date },
    })
    return res.data.data
  },
}
