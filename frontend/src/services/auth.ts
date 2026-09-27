import api from './api'
import { ApiResponse, User } from '@/types'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  full_name: string
  phone?: string
  role?: string
  date_of_birth?: string
  gender?: string
  blood_group?: string
  address?: string
  emergency_contact?: string
}

export interface AuthResponseData {
  access_token: string
  token_type: string
  user: User
}

export const authService = {
  login: async (payload: LoginPayload): Promise<AuthResponseData> => {
    const res = await api.post<ApiResponse<AuthResponseData>>('/auth/login', payload)
    return res.data.data
  },

  register: async (payload: RegisterPayload): Promise<AuthResponseData> => {
    const res = await api.post<ApiResponse<AuthResponseData>>('/auth/register', payload)
    return res.data.data
  },

  getMe: async (): Promise<User> => {
    const res = await api.get<ApiResponse<User>>('/auth/me')
    return res.data.data
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.patch('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}
