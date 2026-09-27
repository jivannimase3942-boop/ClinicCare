import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/admin'
import { useToast } from '@/context/ToastContext'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Modal } from '@/components/ui/Modal'
import { formatDate } from '@/lib/utils'
import { Plus } from 'lucide-react'

export const AdminReports: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [patientId, setPatientId] = useState('')
  const [doctorId, setDoctorId] = useState('')
  const [title, setTitle] = useState('')
  const [reportType, setReportType] = useState('blood_test')
  const [summary, setSummary] = useState('')
  const [status, setStatus] = useState('ready')

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['admin-reports'],
    queryFn: () => adminService.getReports(),
  })

  const { data: patients = [] } = useQuery({
    queryKey: ['admin-patients-list'],
    queryFn: () => adminService.getPatients(),
  })

  const { data: doctors = [] } = useQuery({
    queryKey: ['admin-doctors-list'],
    queryFn: () => adminService.getDoctors(),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminService.updateReportStatus(id, { status }),
    onSuccess: () => {
      showToast('Report updated successfully', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] })
    },
  })

  const createMutation = useMutation({
    mutationFn: () =>
      adminService.createReport({
        patient_id: patientId,
        doctor_id: doctorId || undefined,
        title,
        report_type: reportType,
        summary: summary || undefined,
        status,
      }),
    onSuccess: () => {
      showToast('Diagnostic report created successfully', 'success')
      setIsOpen(false)
      setTitle('')
      setSummary('')
      setPatientId('')
      setDoctorId('')
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError: (err: any) => showToast(err.message || 'Failed to create report', 'error'),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Diagnostic Reports Directory</h1>
          <p className="text-xs text-slate-400">Total lab & radiology reports: {reports.length}</p>
        </div>
        <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsOpen(true)}>
          Add Lab Report
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading reports...</div>
      ) : (
        <div className="bg-slate-800/80 rounded-2xl border border-slate-700 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-700">
              <tr>
                <th className="p-4">Report Title</th>
                <th className="p-4">Patient</th>
                <th className="p-4">Doctor</th>
                <th className="p-4">Type</th>
                <th className="p-4">Date</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60">
              {reports.map((r) => (
                <tr key={r.id} className="hover:bg-slate-700/30 transition">
                  <td className="p-4 font-bold text-white">{r.title}</td>
                  <td className="p-4 text-slate-300">{r.patient_name}</td>
                  <td className="p-4 text-slate-300">{r.doctor_name || 'N/A'}</td>
                  <td className="p-4 uppercase">{r.report_type}</td>
                  <td className="p-4 text-slate-400">{formatDate(r.report_date)}</td>
                  <td className="p-4">
                    <Badge variant={r.status === 'ready' || r.status === 'delivered' ? 'success' : 'warning'}>
                      {r.status}
                    </Badge>
                  </td>
                  <td className="p-4 text-right">
                    {r.status === 'pending' && (
                      <button
                        onClick={() => updateMutation.mutate({ id: r.id, status: 'ready' })}
                        className="px-2.5 py-1 bg-sky-500/20 text-sky-300 rounded border border-sky-500/30 hover:bg-sky-500/30 font-semibold"
                      >
                        Mark Ready
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Report Modal */}
      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Generate New Lab Report" size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Select Patient"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              required
            >
              <option value="">Choose Patient...</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} ({p.email})
                </option>
              ))}
            </Select>

            <Select
              label="Ordering Doctor"
              value={doctorId}
              onChange={(e) => setDoctorId(e.target.value)}
            >
              <option value="">Select Doctor (Optional)...</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name} ({d.specialization})
                </option>
              ))}
            </Select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Report Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Complete Blood Count (CBC)"
              required
            />
            <Select
              label="Report Type"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <option value="blood_test">Blood Test / Pathology</option>
              <option value="radiology">Radiology / X-Ray / CT</option>
              <option value="cardiology">Cardiology / ECG</option>
              <option value="urine_analysis">Urine Analysis</option>
              <option value="other">Other Diagnostic</option>
            </Select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Diagnostic Summary & Findings</label>
            <textarea
              rows={3}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Enter clinical observations, biomarkers, and recommendations..."
              className="w-full bg-slate-50 border rounded-xl p-3 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none text-slate-900"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={!patientId || !title.trim() || createMutation.isPending}
              isLoading={createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Save Report
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
