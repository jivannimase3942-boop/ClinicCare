import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billingService, CollectPaymentPayload } from '@/services/billing'
import { Invoice, RevenueSummary } from '@/types'
import {
  IndianRupee,
  TrendingUp,
  CreditCard,
  Receipt,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  ArrowUpRight,
  Eye,
  Plus,
} from 'lucide-react'
import { useToast } from '@/context/ToastContext'

export const AdminRevenue: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [isCollectModalOpen, setIsCollectModalOpen] = useState(false)
  const [collectAmount, setCollectAmount] = useState<number>(0)
  const [collectMethod, setCollectMethod] = useState<string>('UPI')
  const [collectNotes, setCollectNotes] = useState<string>('')

  // 1. Fetch Revenue Summary
  const { data: summary, isLoading: isSummaryLoading } = useQuery<RevenueSummary>({
    queryKey: ['admin-revenue-summary'],
    queryFn: () => billingService.getRevenueSummary(),
    refetchInterval: 30000,
  })

  // 2. Fetch Invoices
  const { data: invoices = [], isLoading: isInvoicesLoading } = useQuery<Invoice[]>({
    queryKey: ['admin-invoices', statusFilter],
    queryFn: () => billingService.getInvoices({ status: statusFilter || undefined }),
    refetchInterval: 20000,
  })

  // 3. Payment Mutation
  const paymentMutation = useMutation({
    mutationFn: (payload: { id: string; data: CollectPaymentPayload }) =>
      billingService.collectPayment(payload.id, payload.data),
    onSuccess: (updated) => {
      showToast('Payment collected and receipt updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-revenue-summary'] })
      queryClient.invalidateQueries({ queryKey: ['admin-invoices'] })
      setIsCollectModalOpen(false)
      setSelectedInvoice(updated)
    },
    onError: (err: any) => {
      showToast(err?.response?.data?.message || 'Payment collection failed', 'error')
    },
  })

  const handleOpenCollect = (inv: Invoice) => {
    setSelectedInvoice(inv)
    setCollectAmount(inv.balance_due)
    setCollectMethod('UPI')
    setCollectNotes('')
    setIsCollectModalOpen(true)
  }

  const handleCollectSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedInvoice) return
    paymentMutation.mutate({
      id: selectedInvoice.id,
      data: {
        amount: Number(collectAmount),
        payment_method: collectMethod,
        notes: collectNotes || undefined,
      },
    })
  }

  const filteredInvoices = invoices.filter((inv) => {
    const matchesSearch =
      inv.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inv.patient_name && inv.patient_name.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Clinic Finance & Collections
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Revenue & Billing Center</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time OPD collections, receipt tracking, outstanding dues, and tenant revenue metrics.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Today's Collections</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            ₹{(summary?.today_revenue ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1 font-medium">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            7-Day: ₹{(summary?.weekly_revenue ?? 0).toLocaleString('en-IN')}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">30-Day Revenue</span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            ₹{(summary?.monthly_revenue ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-medium">
            {summary?.invoice_count ?? 0} total clinic invoices
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Pending Dues</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-amber-400">
            ₹{(summary?.pending_dues ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-medium">Uncollected balance</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Total Refunds</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <RotateCcw className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-rose-400">
            ₹{(summary?.total_refunds ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-medium">Adjustments & refunds</div>
        </div>
      </div>

      {/* Payment Methods & Revenue Stream Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-sky-400" />
            Payment Method Breakdown
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {summary?.payment_methods && Object.keys(summary.payment_methods).length > 0 ? (
              Object.entries(summary.payment_methods).map(([method, amount]) => (
                <div key={method} className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{method}</p>
                  <p className="text-base font-bold text-white mt-0.5">₹{amount.toLocaleString('en-IN')}</p>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 col-span-full py-4 text-center">No payment transactions recorded yet.</p>
            )}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Receipt className="w-4 h-4 text-emerald-400" />
            Service Stream Revenue
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-800/60 p-3.5 rounded-xl border border-slate-700/60">
              <p className="text-xs font-medium text-slate-400">Consultation OPD</p>
              <p className="text-lg font-bold text-white mt-1">₹{(summary?.consultation_revenue ?? 0).toLocaleString('en-IN')}</p>
            </div>
            <div className="bg-slate-800/60 p-3.5 rounded-xl border border-slate-700/60">
              <p className="text-xs font-medium text-slate-400">Procedures & Labs</p>
              <p className="text-lg font-bold text-white mt-1">₹{(summary?.procedure_revenue ?? 0).toLocaleString('en-IN')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Invoices Table & Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm space-y-4 p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white">Recent Invoices & Billing Records</h2>
            <p className="text-xs text-slate-400">Manage patient charges, payments, and receipts</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search invoice or patient..."
                className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            {/* Filter by status */}
            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-xl border border-slate-700 text-xs">
              {['', 'PENDING', 'PARTIALLY_PAID', 'PAID', 'REFUNDED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition ${
                    statusFilter === st
                      ? 'bg-sky-500 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {st || 'All'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto border border-slate-800 rounded-xl">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-800/80 text-slate-400 font-semibold border-b border-slate-700">
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Patient</th>
                <th className="py-3 px-4">Total</th>
                <th className="py-3 px-4">Paid</th>
                <th className="py-3 px-4">Balance</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {filteredInvoices.length > 0 ? (
                filteredInvoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-white">{inv.invoice_number}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{inv.patient_name || 'Patient'}</div>
                      <div className="text-[11px] text-slate-500">{inv.patient_phone || ''}</div>
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">₹{inv.total_amount.toFixed(2)}</td>
                    <td className="py-3 px-4 font-semibold text-emerald-400">₹{inv.amount_paid.toFixed(2)}</td>
                    <td className="py-3 px-4 font-semibold text-amber-400">₹{inv.balance_due.toFixed(2)}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          inv.status === 'PAID'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : inv.status === 'PARTIALLY_PAID'
                            ? 'bg-sky-500/10 text-sky-400 border-sky-500/20'
                            : inv.status === 'PENDING'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{new Date(inv.created_at).toLocaleDateString('en-IN')}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedInvoice(inv)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium transition"
                        >
                          View
                        </button>
                        {inv.balance_due > 0 && (
                          <button
                            onClick={() => handleOpenCollect(inv)}
                            className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition shadow-sm"
                          >
                            Collect
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No invoices matching current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoice Detail / Receipt Modal */}
      {selectedInvoice && !isCollectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Invoice Details</h3>
                <p className="text-xs text-slate-400 font-mono">{selectedInvoice.invoice_number}</p>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 bg-slate-800/50 p-3 rounded-xl border border-slate-700/60">
                <div>
                  <span className="text-slate-400">Patient:</span>
                  <div className="font-semibold text-white">{selectedInvoice.patient_name}</div>
                  <div className="text-slate-400 text-[11px]">{selectedInvoice.patient_phone}</div>
                </div>
                <div>
                  <span className="text-slate-400">Date:</span>
                  <div className="font-semibold text-white">
                    {new Date(selectedInvoice.created_at).toLocaleString('en-IN')}
                  </div>
                  <div className="text-slate-400 text-[11px]">Status: {selectedInvoice.status}</div>
                </div>
              </div>

              <div>
                <p className="font-semibold text-white mb-2">Itemized Charges</p>
                <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden">
                  {selectedInvoice.items.map((it) => (
                    <div key={it.id} className="p-2.5 flex items-center justify-between bg-slate-800/20">
                      <div>
                        <div className="font-medium text-white">{it.description}</div>
                        <div className="text-[10px] text-slate-500">
                          {it.item_type} · Qty: {it.quantity} × ₹{it.unit_price}
                        </div>
                      </div>
                      <div className="font-bold text-white">₹{it.total_price.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-1 bg-slate-800/40 p-3 rounded-xl text-right">
                <div className="flex justify-between text-slate-400">
                  <span>Subtotal:</span>
                  <span>₹{selectedInvoice.subtotal.toFixed(2)}</span>
                </div>
                {selectedInvoice.discount_amount > 0 && (
                  <div className="flex justify-between text-rose-400">
                    <span>Discount:</span>
                    <span>-₹{selectedInvoice.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                {selectedInvoice.tax_amount > 0 && (
                  <div className="flex justify-between text-slate-400">
                    <span>Tax ({selectedInvoice.tax_rate_percent}%):</span>
                    <span>+₹{selectedInvoice.tax_amount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-white font-bold text-sm pt-1 border-t border-slate-700">
                  <span>Total Amount:</span>
                  <span>₹{selectedInvoice.total_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-emerald-400 font-bold">
                  <span>Amount Paid:</span>
                  <span>₹{selectedInvoice.amount_paid.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-amber-400 font-bold">
                  <span>Balance Due:</span>
                  <span>₹{selectedInvoice.balance_due.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Print Receipt
              </button>
              {selectedInvoice.balance_due > 0 && (
                <button
                  onClick={() => setIsCollectModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                >
                  Collect Payment
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Collect Payment Modal */}
      {selectedInvoice && isCollectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Collect Payment</h3>
                <p className="text-xs text-slate-400">Invoice: {selectedInvoice.invoice_number}</p>
              </div>
              <button
                onClick={() => setIsCollectModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCollectSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Balance Due</label>
                <div className="text-lg font-bold text-amber-400">
                  ₹{selectedInvoice.balance_due.toFixed(2)}
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Payment Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  max={selectedInvoice.balance_due}
                  min={1}
                  required
                  value={collectAmount}
                  onChange={(e) => setCollectAmount(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Payment Method</label>
                <select
                  value={collectMethod}
                  onChange={(e) => setCollectMethod(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-sky-500"
                >
                  <option value="UPI">UPI (Google Pay, PhonePe, Paytm)</option>
                  <option value="CASH">Cash at Desk</option>
                  <option value="CARD">Debit / Credit Card</option>
                  <option value="BANK_TRANSFER">Bank Transfer / NEFT</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Notes / Reference (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. UPI Ref / Cash receipt counter"
                  value={collectNotes}
                  onChange={(e) => setCollectNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCollectModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={paymentMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold disabled:opacity-50"
                >
                  {paymentMutation.isPending ? 'Processing...' : 'Confirm Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default AdminRevenue
