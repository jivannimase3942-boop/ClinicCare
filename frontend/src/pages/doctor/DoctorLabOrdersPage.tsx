import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { labService, CreateLabOrderPayload, EnterResultPayload } from '@/services/lab'
import { patientsApi, PatientRecord } from '@/services/patients'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { LabOrder, LabTest } from '@/types'
import {
  FlaskConical,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Printer,
  Barcode,
  Search,
} from 'lucide-react'

export const DoctorLabOrdersPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<LabOrder | null>(null)
  const [isResultModalOpen, setIsResultModalOpen] = useState(false)
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('')

  // New Order Form state
  const [patientId, setPatientId] = useState('')
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([])
  const [priority, setPriority] = useState('ROUTINE')
  const [clinicalNotes, setClinicalNotes] = useState('')

  // Result entry state
  const [resultEntries, setResultEntries] = useState<Record<string, { val: string; unit: string; range: string; abnormal: boolean; notes: string }>>({})
  const [releaseNotes, setReleaseNotes] = useState('')

  const { data: orders = [], isLoading: loadingOrders } = useQuery({
    queryKey: ['lab-orders', statusFilter],
    queryFn: () => labService.listOrders(undefined, statusFilter || undefined),
  })

  const { data: catalog = [] } = useQuery({
    queryKey: ['lab-tests-catalog'],
    queryFn: () => labService.listTests(),
  })

  const { data: patientsResponse } = useQuery({
    queryKey: ['patients-list'],
    queryFn: () => patientsApi.searchPatients(),
  })
  const patients: PatientRecord[] = patientsResponse?.data || []

  const createOrderMutation = useMutation({
    mutationFn: (payload: CreateLabOrderPayload) => labService.createOrder(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-orders'] })
      setIsOrderModalOpen(false)
      setSelectedTestIds([])
      setClinicalNotes('')
    },
  })

  const collectSampleMutation = useMutation({
    mutationFn: (sampleId: string) => labService.collectSample(sampleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-orders'] })
    },
  })

  const enterResultsMutation = useMutation({
    mutationFn: ({ orderId, results }: { orderId: string; results: EnterResultPayload[] }) =>
      labService.enterResults(orderId, results),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-orders'] })
      setIsResultModalOpen(false)
    },
  })

  const releaseReportMutation = useMutation({
    mutationFn: ({ orderId, notes }: { orderId: string; notes?: string }) =>
      labService.releaseReport(orderId, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lab-orders'] })
      setIsReportModalOpen(false)
      setSelectedOrder(null)
    },
  })

  const handleToggleTest = (id: string) => {
    setSelectedTestIds((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    )
  }

  const handleOpenResultEntry = (order: LabOrder) => {
    setSelectedOrder(order)
    const initial: Record<string, { val: string; unit: string; range: string; abnormal: boolean; notes: string }> = {}
    order.tests.forEach((t) => {
      initial[t.id] = {
        val: '',
        unit: t.unit || '',
        range: t.normal_range || '',
        abnormal: false,
        notes: '',
      }
    })
    setResultEntries(initial)
    setIsResultModalOpen(true)
  }

  const handleSaveResults = () => {
    if (!selectedOrder) return
    const results: EnterResultPayload[] = Object.entries(resultEntries).map(([testId, data]) => {
      const test = selectedOrder.tests.find((t) => t.id === testId)
      return {
        lab_test_id: testId,
        parameter_name: test ? test.name : 'Diagnostic Test',
        result_value: data.val,
        unit: data.unit,
        reference_range: data.range,
        is_abnormal: data.abnormal,
        technician_notes: data.notes,
      }
    })
    enterResultsMutation.mutate({ orderId: selectedOrder.id, results })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ORDERED':
        return <Badge variant="warning">Order Placed</Badge>
      case 'SAMPLE_COLLECTED':
        return <Badge variant="info">Sample Collected</Badge>
      case 'RESULT_READY':
        return <Badge variant="purple">Results Entered</Badge>
      case 'VALIDATED':
        return <Badge variant="success">Validated & Released</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-teal-600" />
            Laboratory & Diagnostics
          </h1>
          <p className="text-sm text-slate-500">
            Order diagnostic tests, track barcode samples, record results, and validate pathology reports.
          </p>
        </div>
        <Button
          onClick={() => setIsOrderModalOpen(true)}
          className="bg-teal-600 hover:bg-teal-700 text-white shadow-sm flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Place Lab Order
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
        {['', 'ORDERED', 'SAMPLE_COLLECTED', 'RESULT_READY', 'VALIDATED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === st
                ? 'bg-teal-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {st === '' ? 'All Orders' : st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Orders List */}
      {loadingOrders ? (
        <div className="text-center py-12 text-slate-500 text-sm">Loading lab orders...</div>
      ) : orders.length === 0 ? (
        <Card className="text-center py-12">
          <FlaskConical className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-700">No laboratory orders found</h3>
          <p className="text-xs text-slate-500 mt-1">Place an order for a patient consultation to begin tracking.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {orders.map((ord) => (
            <Card key={ord.id} className="p-5 border border-slate-200 hover:shadow-md transition">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-teal-700">{ord.order_number}</span>
                    {getStatusBadge(ord.status)}
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                      ord.priority === 'STAT' ? 'bg-red-100 text-red-700' : ord.priority === 'URGENT' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {ord.priority}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 mt-1">
                    Patient: {ord.patient_name || 'Anonymous'}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Ordered by Dr. {ord.doctor_name || 'Physician'} • {new Date(ord.created_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {ord.samples && ord.samples.length > 0 && ord.samples[0].status === 'PENDING' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs text-amber-700 border-amber-300 hover:bg-amber-50"
                      onClick={() => collectSampleMutation.mutate(ord.samples[0].id)}
                    >
                      <Barcode className="w-3.5 h-3.5 mr-1" /> Mark Sample Collected
                    </Button>
                  )}

                  {ord.status === 'SAMPLE_COLLECTED' && (
                    <Button
                      size="sm"
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs"
                      onClick={() => handleOpenResultEntry(ord)}
                    >
                      Enter Test Results
                    </Button>
                  )}

                  {ord.status === 'RESULT_READY' && (
                    <Button
                      size="sm"
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                      onClick={() => {
                        setSelectedOrder(ord)
                        setIsReportModalOpen(true)
                      }}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Validate & Release Report
                    </Button>
                  )}

                  {ord.report && ord.report.is_released && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs text-teal-700 border-teal-300 hover:bg-teal-50"
                      onClick={() => {
                        setSelectedOrder(ord)
                        setIsReportModalOpen(true)
                      }}
                    >
                      <Printer className="w-3.5 h-3.5 mr-1" /> View/Print Report
                    </Button>
                  )}
                </div>
              </div>

              {/* Tests requested */}
              <div className="mt-3 flex flex-wrap gap-2 items-center">
                <span className="text-xs font-medium text-slate-500">Panels:</span>
                {ord.tests.map((t) => (
                  <span key={t.id} className="text-xs bg-slate-100 text-slate-800 px-2.5 py-1 rounded-md font-medium border border-slate-200">
                    {t.name} ({t.code})
                  </span>
                ))}
              </div>

              {/* Barcode details */}
              {ord.samples && ord.samples.length > 0 && (
                <div className="mt-2 text-xs text-slate-500 flex items-center gap-4">
                  <span className="flex items-center gap-1 font-mono">
                    <Barcode className="w-3.5 h-3.5 text-slate-400" />
                    Barcode: {ord.samples[0].barcode_number} ({ord.samples[0].sample_type})
                  </span>
                  {ord.clinical_notes && (
                    <span className="italic">Note: "{ord.clinical_notes}"</span>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Place Lab Order Modal */}
      <Modal
        isOpen={isOrderModalOpen}
        onClose={() => setIsOrderModalOpen(false)}
        title="Place Diagnostic Lab Order"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select Patient *</label>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-white"
            >
              <option value="">-- Choose Patient --</option>
              {patients.map((p: PatientRecord) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} ({p.gender || 'N/A'}) - {p.phone || ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select Diagnostic Tests *</label>
            <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-1">
              {catalog.map((t) => (
                <label
                  key={t.id}
                  className="flex items-center justify-between p-2 hover:bg-slate-50 rounded cursor-pointer text-sm"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selectedTestIds.includes(t.id)}
                      onChange={() => handleToggleTest(t.id)}
                      className="rounded text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <div className="font-medium text-slate-800">{t.name}</div>
                      <div className="text-[11px] text-slate-400">{t.category} • {t.sample_type} • TAT: {t.turnaround_hours}h</div>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-teal-700">₹{t.price}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
              >
                <option value="ROUTINE">ROUTINE</option>
                <option value="URGENT">URGENT</option>
                <option value="STAT">STAT (Emergency)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Clinical Indication</label>
              <input
                type="text"
                value={clinicalNotes}
                onChange={(e) => setClinicalNotes(e.target.value)}
                placeholder="e.g. Rule out anemia, fever for 5 days"
                className="w-full text-sm border border-slate-300 rounded-lg p-2"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsOrderModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-teal-600 hover:bg-teal-700 text-white"
              disabled={!patientId || selectedTestIds.length === 0 || createOrderMutation.isPending}
              onClick={() =>
                createOrderMutation.mutate({
                  patient_id: patientId,
                  test_ids: selectedTestIds,
                  priority,
                  clinical_notes: clinicalNotes,
                })
              }
            >
              {createOrderMutation.isPending ? 'Placing Order...' : 'Confirm Lab Order'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Result Entry Modal */}
      <Modal
        isOpen={isResultModalOpen}
        onClose={() => setIsResultModalOpen(false)}
        title={`Record Test Results: ${selectedOrder?.order_number}`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            Enter test parameter values and reference flags. Results will be marked ready for physician validation.
          </p>

          <div className="space-y-3">
            {selectedOrder?.tests.map((t) => (
              <div key={t.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <div className="font-semibold text-sm text-slate-900">{t.name}</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <div>
                    <label className="text-[11px] text-slate-600 font-medium">Observed Value *</label>
                    <input
                      type="text"
                      placeholder="e.g. 115"
                      value={resultEntries[t.id]?.val || ''}
                      onChange={(e) =>
                        setResultEntries((prev) => ({
                          ...prev,
                          [t.id]: { ...prev[t.id], val: e.target.value },
                        }))
                      }
                      className="w-full text-sm border border-slate-300 rounded p-1.5 bg-white"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600 font-medium">Unit</label>
                    <input
                      type="text"
                      placeholder="mg/dL"
                      value={resultEntries[t.id]?.unit || ''}
                      onChange={(e) =>
                        setResultEntries((prev) => ({
                          ...prev,
                          [t.id]: { ...prev[t.id], unit: e.target.value },
                        }))
                      }
                      className="w-full text-sm border border-slate-300 rounded p-1.5 bg-white"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600 font-medium">Reference Range</label>
                    <input
                      type="text"
                      placeholder="70 - 99"
                      value={resultEntries[t.id]?.range || ''}
                      onChange={(e) =>
                        setResultEntries((prev) => ({
                          ...prev,
                          [t.id]: { ...prev[t.id], range: e.target.value },
                        }))
                      }
                      className="w-full text-sm border border-slate-300 rounded p-1.5 bg-white"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <label className="flex items-center gap-1.5 text-xs text-amber-700 cursor-pointer font-medium">
                    <input
                      type="checkbox"
                      checked={resultEntries[t.id]?.abnormal || false}
                      onChange={(e) =>
                        setResultEntries((prev) => ({
                          ...prev,
                          [t.id]: { ...prev[t.id], abnormal: e.target.checked },
                        }))
                      }
                      className="rounded text-amber-600 focus:ring-amber-500"
                    />
                    Flag as Abnormal
                  </label>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsResultModalOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
              onClick={handleSaveResults}
              disabled={enterResultsMutation.isPending}
            >
              {enterResultsMutation.isPending ? 'Saving Results...' : 'Save Results'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Validate & Print Report Modal */}
      <Modal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        title={selectedOrder?.report?.is_released ? `Diagnostic Report: ${selectedOrder.report.report_number}` : 'Validate & Release Report'}
      >
        <div className="space-y-4">
          {/* Printable Report Preview */}
          <div className="p-4 border-2 border-slate-300 rounded-lg bg-white space-y-4 font-sans text-xs">
            <div className="flex justify-between items-start border-b border-slate-300 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">CLINICCARE DIAGNOSTICS & PATHOLOGY</h2>
                <p className="text-slate-500">Quality Diagnostic Care • ISO/NABL Compliant Workflow Ready</p>
              </div>
              <div className="text-right">
                <span className="font-mono font-bold text-teal-700 text-sm">
                  {selectedOrder?.report?.report_number || 'PENDING RELEASE'}
                </span>
                <p className="text-slate-400">Order: {selectedOrder?.order_number}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 bg-slate-50 p-2.5 rounded border border-slate-200">
              <div>
                <span className="font-semibold text-slate-700">Patient:</span> {selectedOrder?.patient_name}
              </div>
              <div>
                <span className="font-semibold text-slate-700">Attending Doctor:</span> Dr. {selectedOrder?.doctor_name}
              </div>
              <div>
                <span className="font-semibold text-slate-700">Sample Type:</span> {selectedOrder?.samples?.[0]?.sample_type || 'Whole Blood'}
              </div>
              <div>
                <span className="font-semibold text-slate-700">Date:</span> {new Date().toLocaleDateString()}
              </div>
            </div>

            <div className="border border-slate-200 rounded overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-100 text-slate-700 border-b border-slate-200">
                  <tr>
                    <th className="p-2">Investigation</th>
                    <th className="p-2">Observed Value</th>
                    <th className="p-2">Unit</th>
                    <th className="p-2">Biological Ref. Range</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {selectedOrder?.results.map((r) => (
                    <tr key={r.id} className={r.is_abnormal ? 'bg-amber-50 font-semibold' : ''}>
                      <td className="p-2">{r.parameter_name}</td>
                      <td className="p-2">
                        {r.result_value} {r.is_abnormal && <span className="text-amber-700 text-[10px] ml-1">(HIGH)</span>}
                      </td>
                      <td className="p-2">{r.unit || '-'}</td>
                      <td className="p-2">{r.reference_range || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedOrder?.report?.summary_notes && (
              <div className="p-2.5 bg-slate-50 border border-slate-200 rounded">
                <span className="font-semibold text-slate-700">Pathologist Impression:</span>
                <p className="text-slate-600 mt-0.5">{selectedOrder.report.summary_notes}</p>
              </div>
            )}
          </div>

          {/* If not yet released, allow adding impression and releasing */}
          {(!selectedOrder?.report || !selectedOrder.report.is_released) && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Pathologist / Physician Clinical Impression
              </label>
              <textarea
                value={releaseNotes}
                onChange={(e) => setReleaseNotes(e.target.value)}
                placeholder="Enter clinical interpretation, remarks, or recommendation..."
                rows={2}
                className="w-full text-xs border border-slate-300 rounded p-2"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t">
            <Button variant="outline" onClick={() => setIsReportModalOpen(false)}>
              Close
            </Button>
            {selectedOrder?.report?.is_released ? (
              <Button
                className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5"
                onClick={() => window.print()}
              >
                <Printer className="w-4 h-4" /> Print Report
              </Button>
            ) : (
              <Button
                className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5"
                onClick={() =>
                  selectedOrder &&
                  releaseReportMutation.mutate({
                    orderId: selectedOrder.id,
                    notes: releaseNotes,
                  })
                }
                disabled={releaseReportMutation.isPending}
              >
                <CheckCircle2 className="w-4 h-4" /> Sign & Release Report
              </Button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
