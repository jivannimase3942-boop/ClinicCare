import api from '@/services/api'
import {
  ApiResponse,
  LabTest,
  LabOrder,
  LabReport,
} from '@/types'

export interface CreateLabTestPayload {
  name: string
  code: string
  category: string
  sample_type: string
  turnaround_hours: number
  price: number
  normal_range?: string
  unit?: string
}

export interface CreateLabOrderPayload {
  patient_id: string
  appointment_id?: string
  test_ids: string[]
  priority: string
  clinical_notes?: string
}

export interface EnterResultPayload {
  lab_test_id: string
  parameter_name: string
  result_value: string
  unit?: string
  reference_range?: string
  is_abnormal?: boolean
  technician_notes?: string
}

export const labService = {
  listTests: async (category?: string, search?: string): Promise<LabTest[]> => {
    const res = await api.get<ApiResponse<LabTest[]>>('/lab/tests', {
      params: { category, search },
    })
    return res.data.data
  },

  createTest: async (payload: CreateLabTestPayload): Promise<LabTest> => {
    const res = await api.post<ApiResponse<LabTest>>('/lab/tests', payload)
    return res.data.data
  },

  createOrder: async (payload: CreateLabOrderPayload): Promise<LabOrder> => {
    const res = await api.post<ApiResponse<LabOrder>>('/lab/orders', payload)
    return res.data.data
  },

  listOrders: async (patientId?: string, status?: string): Promise<LabOrder[]> => {
    const res = await api.get<ApiResponse<LabOrder[]>>('/lab/orders', {
      params: { patient_id: patientId, status },
    })
    return res.data.data
  },

  getOrder: async (id: string): Promise<LabOrder> => {
    const res = await api.get<ApiResponse<LabOrder>>(`/lab/orders/${id}`)
    return res.data.data
  },

  collectSample: async (sampleId: string): Promise<LabOrder> => {
    const res = await api.post<ApiResponse<LabOrder>>(`/lab/samples/${sampleId}/collect`)
    return res.data.data
  },

  enterResults: async (orderId: string, results: EnterResultPayload[]): Promise<LabOrder> => {
    const res = await api.post<ApiResponse<LabOrder>>(`/lab/orders/${orderId}/results`, { results })
    return res.data.data
  },

  releaseReport: async (orderId: string, summaryNotes?: string): Promise<LabReport> => {
    const res = await api.post<ApiResponse<LabReport>>(`/lab/orders/${orderId}/release`, { summary_notes: summaryNotes })
    return res.data.data
  },

  listPatientOrders: async (patientId: string): Promise<LabOrder[]> => {
    const res = await api.get<ApiResponse<LabOrder[]>>(`/lab/patient/${patientId}`)
    return res.data.data
  },
}
