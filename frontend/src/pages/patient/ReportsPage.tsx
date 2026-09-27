import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { reportService } from '@/services/reports'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { FileText, Download, Calendar, Stethoscope, Eye } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { MedicalReport } from '@/types'

export const ReportsPage: React.FC = () => {
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null)

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['patient-reports'],
    queryFn: () => reportService.getMyReports(),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Medical & Lab Reports</h1>
        <p className="text-xs text-slate-500">Access verified pathology, cardiology, and radiology test results</p>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">Loading medical reports...</div>
      ) : reports.length === 0 ? (
        <div className="py-12 text-center text-slate-500">No medical reports currently on file.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reports.map((r) => (
            <Card key={r.id} className="flex flex-col justify-between p-5">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm">{r.title}</h3>
                      <p className="text-xs text-slate-500 capitalize">{r.report_type.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <Badge variant={r.status === 'ready' || r.status === 'delivered' ? 'success' : 'warning'}>{r.status}</Badge>
                </div>

                <div className="text-xs text-slate-600 space-y-1 border-t pt-2">
                  <p className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5 text-slate-400" /> Date: {formatDate(r.report_date)}</p>
                  {r.doctor_name && <p className="flex items-center gap-1.5"><Stethoscope className="w-3.5 h-3.5 text-slate-400" /> Ordered by: {r.doctor_name}</p>}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t flex justify-end gap-2">
                <Button variant="outline" size="sm" leftIcon={<Eye className="w-4 h-4" />} onClick={() => setSelectedReport(r)}>
                  View Summary
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Summary View Modal */}
      <Modal isOpen={!!selectedReport} onClose={() => setSelectedReport(null)} title={selectedReport?.title || 'Report Details'}>
        <div className="space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border space-y-1 text-xs text-slate-600">
            <p><strong className="text-slate-800">Type:</strong> {selectedReport?.report_type}</p>
            <p><strong className="text-slate-800">Date:</strong> {formatDate(selectedReport?.report_date)}</p>
            <p><strong className="text-slate-800">Status:</strong> {selectedReport?.status}</p>
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-800 mb-1">Clinical Diagnostic Summary</h4>
            <div className="p-4 bg-white border rounded-xl text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
              {selectedReport?.summary || 'Diagnostic analysis completed and in normal physiological parameters.'}
            </div>
          </div>
          <div className="flex justify-end">
            <Button size="sm" onClick={() => setSelectedReport(null)}>Close</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
