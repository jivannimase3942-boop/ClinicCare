import api from './api'
import { ApiResponse, Invoice, RevenueSummary } from '../types'

export interface CreateInvoicePayload {
  patient_id: string
  appointment_id?: string
  doctor_id?: string
  items: Array<{
    item_type: string
    description: string
    quantity: number
    unit_price: number
  }>
  discount_amount?: number
  tax_rate_percent?: number
  notes?: string
}

export interface CollectPaymentPayload {
  amount: number
  payment_method: 'CASH' | 'UPI' | 'CARD' | 'ONLINE_GATEWAY' | 'BANK_TRANSFER' | string
  transaction_reference?: string
  notes?: string
}

export interface ProcessRefundPayload {
  amount: number
  reason: string
}

export const billingService = {
  createInvoice: async (payload: CreateInvoicePayload): Promise<Invoice> => {
    const res = await api.post<ApiResponse<Invoice>>('/billing/invoices', payload)
    return res.data.data
  },

  getInvoices: async (params?: { patient_id?: string; status?: string }): Promise<Invoice[]> => {
    const res = await api.get<ApiResponse<Invoice[]>>('/billing/invoices', { params })
    return res.data.data
  },

  getInvoiceById: async (id: string): Promise<Invoice> => {
    const res = await api.get<ApiResponse<Invoice>>(`/billing/invoices/${id}`)
    return res.data.data
  },

  collectPayment: async (invoiceId: string, payload: CollectPaymentPayload): Promise<Invoice> => {
    const res = await api.post<ApiResponse<Invoice>>(`/billing/invoices/${invoiceId}/payments`, payload)
    return res.data.data
  },

  processRefund: async (invoiceId: string, payload: ProcessRefundPayload): Promise<Invoice> => {
    const res = await api.post<ApiResponse<Invoice>>(`/billing/invoices/${invoiceId}/refund`, payload)
    return res.data.data
  },

  getRevenueSummary: async (): Promise<RevenueSummary> => {
    const res = await api.get<ApiResponse<RevenueSummary>>('/billing/revenue')
    return res.data.data
  },

  createOnlineOrder: async (invoiceId: string) => {
    const res = await api.post<ApiResponse<any>>(`/billing/online-order?invoice_id=${invoiceId}`)
    return res.data
  },
}
