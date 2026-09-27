import api from './api'
import {
  ApiResponse,
  AdminDashboardStats,
  Doctor,
  Department,
  Appointment,
  MedicalReport,
  Feedback,
  Escalation,
  VoiceCallRequest,
  AIConversation,
  ErrorLog,
} from '@/types'

export const adminService = {
  getStats: async (): Promise<AdminDashboardStats> => {
    const res = await api.get<ApiResponse<AdminDashboardStats>>('/admin/stats')
    return res.data.data
  },

  getPatients: async (search?: string): Promise<any[]> => {
    const res = await api.get<ApiResponse<any[]>>('/admin/patients', { params: { search } })
    return res.data.data
  },

  getDoctors: async (): Promise<Doctor[]> => {
    const res = await api.get<ApiResponse<Doctor[]>>('/admin/doctors')
    return res.data.data
  },

  createDepartment: async (payload: { name: string; description?: string; icon?: string }): Promise<Department> => {
    const res = await api.post<ApiResponse<Department>>('/admin/departments', payload)
    return res.data.data
  },

  getAppointments: async (params?: { doctor_id?: string; patient_id?: string; date?: string; status?: string }): Promise<Appointment[]> => {
    const res = await api.get<ApiResponse<Appointment[]>>('/admin/appointments', { params })
    return res.data.data
  },

  updateAppointmentStatus: async (id: string, status: string): Promise<Appointment> => {
    const res = await api.patch<ApiResponse<Appointment>>(`/admin/appointments/${id}/status`, { status })
    return res.data.data
  },

  getReports: async (status?: string): Promise<MedicalReport[]> => {
    const res = await api.get<ApiResponse<MedicalReport[]>>('/admin/reports', { params: { status } })
    return res.data.data
  },

  createReport: async (payload: { patient_id: string; doctor_id?: string; title: string; report_type: string; summary?: string; status?: string }): Promise<MedicalReport> => {
    const res = await api.post<ApiResponse<MedicalReport>>('/admin/reports', payload)
    return res.data.data
  },

  updateReportStatus: async (id: string, payload: { status: string; summary?: string; file_url?: string }): Promise<MedicalReport> => {
    const res = await api.patch<ApiResponse<MedicalReport>>(`/admin/reports/${id}/status`, payload)
    return res.data.data
  },

  getFeedback: async (rating?: number): Promise<Feedback[]> => {
    const res = await api.get<ApiResponse<Feedback[]>>('/admin/feedback', { params: { rating } })
    return res.data.data
  },

  getEscalations: async (params?: { status?: string; priority?: string }): Promise<Escalation[]> => {
    const res = await api.get<ApiResponse<Escalation[]>>('/admin/escalations', { params })
    return res.data.data
  },

  updateEscalation: async (id: string, payload: { status?: string; assigned_to?: string; admin_notes?: string }): Promise<Escalation> => {
    const res = await api.patch<ApiResponse<Escalation>>(`/admin/escalations/${id}`, payload)
    return res.data.data
  },

  getVoiceCalls: async (status?: string): Promise<VoiceCallRequest[]> => {
    const res = await api.get<ApiResponse<VoiceCallRequest[]>>('/admin/voice-calls', { params: { status } })
    return res.data.data
  },

  updateVoiceCall: async (id: string, payload: { status: string; notes?: string }): Promise<VoiceCallRequest> => {
    const res = await api.patch<ApiResponse<VoiceCallRequest>>(`/admin/voice-calls/${id}`, payload)
    return res.data.data
  },

  getConversations: async (limit: number = 50): Promise<AIConversation[]> => {
    const res = await api.get<ApiResponse<AIConversation[]>>('/admin/conversations', { params: { limit } })
    return res.data.data
  },

  getErrorLogs: async (limit: number = 50): Promise<ErrorLog[]> => {
    const res = await api.get<ApiResponse<ErrorLog[]>>('/admin/errors', { params: { limit } })
    return res.data.data
  },
}
