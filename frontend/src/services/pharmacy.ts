import api from '@/services/api'
import {
  ApiResponse,
  Supplier,
  StockBatch,
  StockTransaction,
  StockAlert,
} from '@/types'

export interface CreateSupplierPayload {
  name: string
  contact_person?: string
  phone?: string
  email?: string
  gstin?: string
  dl_number?: string
  address?: string
}

export interface CreateBatchPayload {
  medicine_id: string
  supplier_id?: string
  batch_number: string
  expiry_date: string
  purchase_price: number
  mrp: number
  sale_price: number
  initial_quantity: number
  reorder_threshold: number
}

export interface AdjustStockPayload {
  batch_id: string
  transaction_type: string
  quantity: number
  reason?: string
  unit_price?: number
}

export interface DispenseItemPayload {
  batch_id: string
  quantity: number
}

export interface DispenseRequestPayload {
  patient_id: string
  appointment_id?: string
  prescription_id?: string
  items: DispenseItemPayload[]
  payment_method: string
  notes?: string
}

export interface DispenseResponse {
  invoice_id: string
  invoice_number: string
  total_amount: number
  status: string
  items_dispensed: number
  message: string
}

export const pharmacyService = {
  listSuppliers: async (): Promise<Supplier[]> => {
    const res = await api.get<ApiResponse<Supplier[]>>('/pharmacy/suppliers')
    return res.data.data
  },

  createSupplier: async (payload: CreateSupplierPayload): Promise<Supplier> => {
    const res = await api.post<ApiResponse<Supplier>>('/pharmacy/suppliers', payload)
    return res.data.data
  },

  listBatches: async (medicineId?: string): Promise<StockBatch[]> => {
    const res = await api.get<ApiResponse<StockBatch[]>>('/pharmacy/batches', {
      params: { medicine_id: medicineId },
    })
    return res.data.data
  },

  createBatch: async (payload: CreateBatchPayload): Promise<StockBatch> => {
    const res = await api.post<ApiResponse<StockBatch>>('/pharmacy/batches', payload)
    return res.data.data
  },

  getAlerts: async (): Promise<StockAlert[]> => {
    const res = await api.get<ApiResponse<StockAlert[]>>('/pharmacy/alerts')
    return res.data.data
  },

  adjustStock: async (payload: AdjustStockPayload): Promise<StockBatch> => {
    const res = await api.post<ApiResponse<StockBatch>>('/pharmacy/adjustments', payload)
    return res.data.data
  },

  listTransactions: async (batchId?: string, medicineId?: string): Promise<StockTransaction[]> => {
    const res = await api.get<ApiResponse<StockTransaction[]>>('/pharmacy/transactions', {
      params: { batch_id: batchId, medicine_id: medicineId },
    })
    return res.data.data
  },

  dispenseAndBill: async (payload: DispenseRequestPayload): Promise<DispenseResponse> => {
    const res = await api.post<ApiResponse<DispenseResponse>>('/pharmacy/dispense', payload)
    return res.data.data
  },
}
