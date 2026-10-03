import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { billingService } from '@/services/billing'
import { Invoice } from '@/types'
import {
  Receipt,
  IndianRupee,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  Printer,
  CreditCard,
} from 'lucide-react'
import { useToast } from '@/context/ToastContext'

export const PatientInvoicesPage: React.FC = () => {
  const { showToast } = useToast()
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [isProcessingPayment, setIsProcessingPayment] = useState(false)

  const { data: invoices = [], isLoading } = useQuery<Invoice[]>({
    queryKey: ['patient-invoices'],
    queryFn: () => billingService.getInvoices(),
  })

  const totalDues = invoices.reduce((acc, inv) => acc + (inv.status !== 'PAID' ? inv.balance_due : 0), 0)

  const handleOnlinePay = async (inv: Invoice) => {
    setIsProcessingPayment(true)
    try {
      const res = await billingService.createOnlineOrder(inv.id)
      if (!res.data?.gateway_configured) {
        showToast(
          res.message || 'Online payment gateway is not configured. Please pay via Cash or UPI at reception desk.',
          'info'
        )
      } else {
        showToast('Online payment checkout ready (Razorpay).', 'success')
      }
    } catch (err: any) {
      showToast(err?.response?.data?.message || 'Unable to initiate online payment.', 'error')
    } finally {
      setIsProcessingPayment(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Loading your billing invoices...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-sky-950/40 p-6 rounded-2xl border border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Patient Portal
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Billing & Receipts</h1>
          <p className="text-xs text-slate-300 mt-1">
            View consultation invoices, download official receipts, and check outstanding balances.
          </p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-xl flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
            <IndianRupee className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Total Outstanding</p>
            <p className="text-xl font-black text-amber-400">₹{totalDues.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Invoices List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-5 space-y-4">
        <h2 className="text-sm font-bold text-slate-900">Your Invoices ({invoices.length})</h2>

        {invoices.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {invoices.map((inv) => (
              <div
                key={inv.id}
                className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 p-2 rounded-xl transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-slate-900">{inv.invoice_number}</span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        inv.status === 'PAID'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : inv.status === 'PARTIALLY_PAID'
                          ? 'bg-sky-50 text-sky-700 border-sky-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {inv.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Clinic: {inv.clinic_name || 'ClinicCare'} · Date: {new Date(inv.created_at).toLocaleDateString('en-IN')}
                  </p>
                  <div className="text-xs text-slate-600">
                    Total: <span className="font-semibold text-slate-900">₹{inv.total_amount.toFixed(2)}</span>
                    {inv.balance_due > 0 && (
                      <span className="text-amber-600 font-semibold ml-2">(Balance: ₹{inv.balance_due.toFixed(2)})</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSelectedInvoice(inv)}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition"
                  >
                    View Breakdown
                  </button>
                  {inv.balance_due > 0 && (
                    <button
                      onClick={() => handleOnlinePay(inv)}
                      disabled={isProcessingPayment}
                      className="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
                    >
                      <CreditCard className="w-3.5 h-3.5" />
                      Pay Online
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-xs space-y-2">
            <Receipt className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="font-semibold">No invoices found</p>
            <p className="text-slate-400">Invoices will appear here once you visit the clinic for consultation.</p>
          </div>
        )}
      </div>

      {/* Invoice Breakdown Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Invoice Receipt</h3>
                <p className="text-xs text-slate-500 font-mono">{selectedInvoice.invoice_number}</p>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                <div className="font-bold text-slate-900">{selectedInvoice.clinic_name || 'ClinicCare'}</div>
                <div className="text-slate-500">{selectedInvoice.clinic_address || 'India'}</div>
                <div className="text-slate-500">Contact: {selectedInvoice.clinic_phone || '+91 800 555 0100'}</div>
              </div>

              <div>
                <p className="font-semibold text-slate-700 mb-2">Itemized Services</p>
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                  {selectedInvoice.items.map((it) => (
                    <div key={it.id} className="p-2.5 flex items-center justify-between">
                      <div>
                        <div className="font-medium text-slate-800">{it.description}</div>
                        <div className="text-[10px] text-slate-400">Qty: {it.quantity}</div>
                      </div>
                      <div className="font-bold text-slate-900">₹{it.total_price.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-1 bg-slate-50 p-3 rounded-xl text-right">
                <div className="flex justify-between text-slate-500">
                  <span>Subtotal:</span>
                  <span>₹{selectedInvoice.subtotal.toFixed(2)}</span>
                </div>
                {selectedInvoice.discount_amount > 0 && (
                  <div className="flex justify-between text-rose-600">
                    <span>Discount:</span>
                    <span>-₹{selectedInvoice.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                {selectedInvoice.tax_amount > 0 && (
                  <div className="flex justify-between text-slate-500">
                    <span>Taxes:</span>
                    <span>+₹{selectedInvoice.tax_amount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-slate-900 font-bold text-sm pt-1 border-t border-slate-200">
                  <span>Total:</span>
                  <span>₹{selectedInvoice.total_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-emerald-600 font-bold">
                  <span>Paid:</span>
                  <span>₹{selectedInvoice.amount_paid.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-amber-600 font-bold">
                  <span>Balance:</span>
                  <span>₹{selectedInvoice.balance_due.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50"
              >
                Print
              </button>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
export default PatientInvoicesPage
