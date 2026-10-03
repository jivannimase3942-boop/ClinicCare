import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  pharmacyService,
  CreateBatchPayload,
  CreateSupplierPayload,
  AdjustStockPayload,
} from '@/services/pharmacy'
import { prescriptionService } from '@/services/prescriptions'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { StockBatch, StockAlert, StockTransaction, Supplier, Medicine } from '@/types'
import {
  Pill,
  Plus,
  AlertTriangle,
  Clock,
  Building2,
  History,
  ShieldAlert,
  ArrowUpDown,
  Search,
} from 'lucide-react'

export const AdminPharmacyPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'batches' | 'alerts' | 'suppliers' | 'ledger'>('batches')

  // Modals
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false)
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false)
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false)
  const [selectedBatch, setSelectedBatch] = useState<StockBatch | null>(null)

  // Batch Form State
  const [medicineId, setMedicineId] = useState('')
  const [supplierId, setSupplierId] = useState('')
  const [batchNumber, setBatchNumber] = useState('')
  const [expiryDate, setExpiryDate] = useState('')
  const [purchasePrice, setPurchasePrice] = useState(0)
  const [mrp, setMrp] = useState(0)
  const [salePrice, setSalePrice] = useState(0)
  const [initialQty, setInitialQty] = useState(50)
  const [reorderThreshold, setReorderThreshold] = useState(15)

  // Supplier Form State
  const [supplierName, setSupplierName] = useState('')
  const [contactPerson, setContactPerson] = useState('')
  const [phone, setPhone] = useState('')
  const [gstin, setGstin] = useState('')
  const [dlNumber, setDlNumber] = useState('')

  // Adjust Form State
  const [adjustType, setAdjustType] = useState('DAMAGE')
  const [adjustQty, setAdjustQty] = useState(-5)
  const [adjustReason, setAdjustReason] = useState('')

  // Queries
  const { data: batches = [], isLoading: loadingBatches } = useQuery({
    queryKey: ['pharmacy-batches'],
    queryFn: () => pharmacyService.listBatches(),
  })

  const { data: alerts = [] } = useQuery({
    queryKey: ['pharmacy-alerts'],
    queryFn: () => pharmacyService.getAlerts(),
  })

  const { data: suppliers = [] } = useQuery({
    queryKey: ['pharmacy-suppliers'],
    queryFn: () => pharmacyService.listSuppliers(),
  })

  const { data: medicines = [] } = useQuery({
    queryKey: ['medicines-catalog'],
    queryFn: () => prescriptionService.listMedicines(),
  })

  const { data: transactions = [] } = useQuery({
    queryKey: ['pharmacy-transactions'],
    queryFn: () => pharmacyService.listTransactions(),
    enabled: activeTab === 'ledger',
  })

  // Mutations
  const createBatchMutation = useMutation({
    mutationFn: (p: CreateBatchPayload) => pharmacyService.createBatch(p),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy-batches'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-alerts'] })
      setIsBatchModalOpen(false)
      setBatchNumber('')
    },
  })

  const createSupplierMutation = useMutation({
    mutationFn: (p: CreateSupplierPayload) => pharmacyService.createSupplier(p),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy-suppliers'] })
      setIsSupplierModalOpen(false)
      setSupplierName('')
    },
  })

  const adjustStockMutation = useMutation({
    mutationFn: (p: AdjustStockPayload) => pharmacyService.adjustStock(p),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pharmacy-batches'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['pharmacy-transactions'] })
      setIsAdjustModalOpen(false)
      setSelectedBatch(null)
    },
  })

  const expiredCount = alerts.filter((a) => a.alert_type === 'EXPIRED').length
  const nearExpiryCount = alerts.filter((a) => a.alert_type === 'NEAR_EXPIRY').length
  const lowStockCount = alerts.filter((a) => a.alert_type === 'LOW_STOCK').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-teal-600" />
            Pharmacy & Inventory Management
          </h1>
          <p className="text-sm text-slate-500">
            Track batch expiration, FEFO stock distribution, vendor procurement, and auditable inventory transactions.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setIsSupplierModalOpen(true)}
            className="flex items-center gap-1.5"
          >
            <Building2 className="w-4 h-4" /> Add Supplier
          </Button>
          <Button
            onClick={() => setIsBatchModalOpen(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Inbound Stock (New Batch)
          </Button>
        </div>
      </div>

      {/* Safety Alert Banner if expired items exist */}
      {expiredCount > 0 && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-800">
          <ShieldAlert className="w-6 h-6 text-red-600 shrink-0" />
          <div className="text-xs">
            <span className="font-bold">Regulatory Safety Warning:</span> {expiredCount} medicine batch(es) have expired.
            Dispensing is automatically blocked by the system safety engine. Please quarantine and adjust stock.
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-teal-500">
          <div className="text-xs text-slate-500 font-medium">Active Stock Batches</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{batches.length}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Tracked in clinic dispensary</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="text-xs text-slate-500 font-medium">Near Expiry (60 Days)</div>
          <div className="text-2xl font-bold text-amber-700 mt-1">{nearExpiryCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Prioritize FEFO dispensing</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-red-500">
          <div className="text-xs text-slate-500 font-medium">Expired Batches</div>
          <div className="text-2xl font-bold text-red-700 mt-1">{expiredCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Dispense strictly blocked</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-indigo-500">
          <div className="text-xs text-slate-500 font-medium">Low Stock Alerts</div>
          <div className="text-2xl font-bold text-indigo-700 mt-1">{lowStockCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Below reorder threshold</div>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        {[
          { key: 'batches', label: 'Stock & Batches', count: batches.length },
          { key: 'alerts', label: 'Inventory Alerts', count: alerts.length },
          { key: 'suppliers', label: 'Vendors & Suppliers', count: suppliers.length },
          { key: 'ledger', label: 'Movement Ledger', count: transactions.length },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`pb-3 text-sm font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === tab.key
                ? 'border-teal-600 text-teal-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className="text-[11px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-full">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab: Stock & Batches */}
      {activeTab === 'batches' && (
        <Card className="p-0 overflow-hidden border border-slate-200">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="p-3">Medicine</th>
                  <th className="p-3">Batch Number</th>
                  <th className="p-3">Expiry Date</th>
                  <th className="p-3">Stock Available</th>
                  <th className="p-3">Pricing (Cost/MRP/Sale)</th>
                  <th className="p-3">Supplier</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-3">
                      <div className="font-semibold text-slate-900">{b.medicine_name}</div>
                      <div className="text-[11px] text-slate-400">{b.generic_name} • {b.dosage_form}</div>
                    </td>
                    <td className="p-3 font-mono font-bold text-slate-800">{b.batch_number}</td>
                    <td className="p-3">
                      <span className={`inline-flex items-center gap-1 font-medium ${
                        b.is_expired ? 'text-red-700' : b.is_near_expiry ? 'text-amber-700' : 'text-slate-700'
                      }`}>
                        {b.expiry_date}
                        {b.is_expired && <Badge variant="danger">Expired</Badge>}
                        {b.is_near_expiry && <Badge variant="warning">Near Expiry</Badge>}
                      </span>
                    </td>
                    <td className="p-3">
                      <div className="font-bold text-slate-900">{b.current_quantity} units</div>
                      <div className="text-[11px] text-slate-400">Min: {b.reorder_threshold}</div>
                    </td>
                    <td className="p-3">
                      ₹{b.purchase_price} / ₹{b.mrp} / <span className="font-bold text-teal-700">₹{b.sale_price}</span>
                    </td>
                    <td className="p-3 text-slate-600">{b.supplier_name || 'Standard'}</td>
                    <td className="p-3 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        onClick={() => {
                          setSelectedBatch(b)
                          setIsAdjustModalOpen(true)
                        }}
                      >
                        <ArrowUpDown className="w-3.5 h-3.5 mr-1" /> Adjust Stock
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab: Alerts */}
      {activeTab === 'alerts' && (
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <Card className="text-center py-12 text-slate-500 text-sm">
              All inventory levels are optimal and within safe expiry ranges.
            </Card>
          ) : (
            alerts.map((al, idx) => (
              <Card key={idx} className={`p-4 border-l-4 ${
                al.alert_type === 'EXPIRED' ? 'border-l-red-500 bg-red-50/30' :
                al.alert_type === 'NEAR_EXPIRY' ? 'border-l-amber-500 bg-amber-50/30' : 'border-l-indigo-500'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant={al.alert_type === 'EXPIRED' ? 'danger' : 'warning'}>
                        {al.alert_type}
                      </Badge>
                      <h4 className="font-bold text-sm text-slate-900">{al.medicine_name}</h4>
                      <span className="font-mono text-xs text-slate-500">Batch: {al.batch_number}</span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{al.message}</p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <div>Current Stock: <span className="font-bold text-slate-800">{al.current_quantity}</span></div>
                    <div>Expiry: {al.expiry_date}</div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab: Suppliers */}
      {activeTab === 'suppliers' && (
        <Card className="p-0 overflow-hidden border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-3">Vendor / Distributor</th>
                <th className="p-3">Contact Person</th>
                <th className="p-3">Phone & Email</th>
                <th className="p-3">GSTIN (India)</th>
                <th className="p-3">Drug License</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {suppliers.map((s) => (
                <tr key={s.id}>
                  <td className="p-3 font-semibold text-slate-900">{s.name}</td>
                  <td className="p-3 text-slate-700">{s.contact_person || 'N/A'}</td>
                  <td className="p-3 text-slate-600">{s.phone} • {s.email}</td>
                  <td className="p-3 font-mono text-slate-700">{s.gstin || 'Unspecified'}</td>
                  <td className="p-3 font-mono text-slate-700">{s.dl_number || 'Unspecified'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Tab: Movement Ledger */}
      {activeTab === 'ledger' && (
        <Card className="p-0 overflow-hidden border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Type</th>
                <th className="p-3">Medicine & Batch</th>
                <th className="p-3">Delta Qty</th>
                <th className="p-3">Balance After</th>
                <th className="p-3">Reason / Reference</th>
                <th className="p-3">Operator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td className="p-3 text-slate-500">{new Date(tx.created_at).toLocaleString()}</td>
                  <td className="p-3">
                    <Badge variant={tx.transaction_type === 'PURCHASE' ? 'success' : tx.transaction_type === 'SALE' ? 'info' : 'warning'}>
                      {tx.transaction_type}
                    </Badge>
                  </td>
                  <td className="p-3 font-medium text-slate-900">{tx.medicine_name} ({tx.batch_number})</td>
                  <td className="p-3 font-bold font-mono">
                    {tx.quantity > 0 ? `+${tx.quantity}` : tx.quantity}
                  </td>
                  <td className="p-3 font-bold text-slate-800">{tx.balance_after}</td>
                  <td className="p-3 text-slate-600">{tx.reason || '-'}</td>
                  <td className="p-3 text-slate-500">{tx.actor_name || 'System'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Modal: New Batch Inbound */}
      <Modal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        title="Inbound Stock Entry (New Batch)"
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Select Medicine Master *</label>
            <select
              value={medicineId}
              onChange={(e) => setMedicineId(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
            >
              <option value="">-- Choose Medicine --</option>
              {medicines.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.brand_name} ({m.generic_name} {m.strength})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Supplier / Distributor</label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
              >
                <option value="">-- Select Supplier --</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Batch Number *</label>
              <input
                type="text"
                value={batchNumber}
                onChange={(e) => setBatchNumber(e.target.value)}
                placeholder="e.g. B2026-X1"
                className="w-full text-xs border border-slate-300 rounded p-2 font-mono uppercase"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Expiry Date *</label>
              <input
                type="date"
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Initial Quantity (Pcs/Strips) *</label>
              <input
                type="number"
                value={initialQty}
                onChange={(e) => setInitialQty(Number(e.target.value))}
                min={1}
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Cost Price (₹)</label>
              <input
                type="number"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(Number(e.target.value))}
                step="0.1"
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">MRP (₹)</label>
              <input
                type="number"
                value={mrp}
                onChange={(e) => setMrp(Number(e.target.value))}
                step="0.1"
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Sale Price (₹)</label>
              <input
                type="number"
                value={salePrice}
                onChange={(e) => setSalePrice(Number(e.target.value))}
                step="0.1"
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsBatchModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-teal-600 hover:bg-teal-700 text-white"
              disabled={!medicineId || !batchNumber || !expiryDate || createBatchMutation.isPending}
              onClick={() =>
                createBatchMutation.mutate({
                  medicine_id: medicineId,
                  supplier_id: supplierId || undefined,
                  batch_number: batchNumber,
                  expiry_date: expiryDate,
                  purchase_price: purchasePrice,
                  mrp,
                  sale_price: salePrice,
                  initial_quantity: initialQty,
                  reorder_threshold: reorderThreshold,
                })
              }
            >
              {createBatchMutation.isPending ? 'Logging Inbound...' : 'Record Inbound Batch'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Add Supplier */}
      <Modal
        isOpen={isSupplierModalOpen}
        onClose={() => setIsSupplierModalOpen(false)}
        title="Register Vendor / Pharmaceutical Supplier"
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Distributor / Vendor Name *</label>
            <input
              type="text"
              value={supplierName}
              onChange={(e) => setSupplierName(e.target.value)}
              placeholder="e.g. MedPlus Pharma Distributors Ltd"
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Contact Person</label>
              <input
                type="text"
                value={contactPerson}
                onChange={(e) => setContactPerson(e.target.value)}
                placeholder="Ramesh Kumar"
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Phone</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">GSTIN Number (India)</label>
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value)}
                placeholder="27AABCU9603R1ZM"
                className="w-full text-xs border border-slate-300 rounded p-2 font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Drug License (DL)</label>
              <input
                type="text"
                value={dlNumber}
                onChange={(e) => setDlNumber(e.target.value)}
                placeholder="MH-TZ-123456"
                className="w-full text-xs border border-slate-300 rounded p-2 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsSupplierModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-teal-600 hover:bg-teal-700 text-white"
              disabled={!supplierName || createSupplierMutation.isPending}
              onClick={() =>
                createSupplierMutation.mutate({
                  name: supplierName,
                  contact_person: contactPerson,
                  phone,
                  gstin,
                  dl_number: dlNumber,
                })
              }
            >
              {createSupplierMutation.isPending ? 'Registering...' : 'Register Supplier'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal: Adjust Stock */}
      <Modal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        title={`Adjust Stock: ${selectedBatch?.medicine_name} (${selectedBatch?.batch_number})`}
      >
        <div className="space-y-4 text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div>Current Stock: <span className="font-bold text-slate-800">{selectedBatch?.current_quantity} units</span></div>
            <div>Expiry: {selectedBatch?.expiry_date}</div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Adjustment Type</label>
              <select
                value={adjustType}
                onChange={(e) => setAdjustType(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
              >
                <option value="DAMAGE">DAMAGE (Waste / Broken)</option>
                <option value="RETURN">RETURN (To Vendor)</option>
                <option value="ADJUSTMENT">AUDIT ADJUSTMENT</option>
                <option value="TRANSFER">TRANSFER</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Quantity Delta</label>
              <input
                type="number"
                value={adjustQty}
                onChange={(e) => setAdjustQty(Number(e.target.value))}
                className="w-full text-xs border border-slate-300 rounded p-2 font-mono"
              />
              <span className="text-[10px] text-slate-400">Negative to deduct, positive to add.</span>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Reason for Audit Ledger *</label>
            <input
              type="text"
              value={adjustReason}
              onChange={(e) => setAdjustReason(e.target.value)}
              placeholder="e.g. Expired batch discarded, broken during transport"
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsAdjustModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
              disabled={!adjustReason || adjustStockMutation.isPending}
              onClick={() =>
                selectedBatch &&
                adjustStockMutation.mutate({
                  batch_id: selectedBatch.id,
                  transaction_type: adjustType,
                  quantity: adjustQty,
                  reason: adjustReason,
                })
              }
            >
              {adjustStockMutation.isPending ? 'Logging Adjustment...' : 'Confirm Stock Adjustment'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
