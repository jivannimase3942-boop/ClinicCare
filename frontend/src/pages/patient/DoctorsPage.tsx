import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { doctorService } from '@/services/doctors'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Search, Stethoscope, Calendar, MapPin, Award } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

export const DoctorsPage: React.FC = () => {
  const [search, setSearch] = useState('')
  const [selectedDept, setSelectedDept] = useState<string>('')
  const navigate = useNavigate()

  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => doctorService.getDepartments(),
  })

  const { data: doctors = [], isLoading } = useQuery({
    queryKey: ['doctors', selectedDept, search],
    queryFn: () => doctorService.getDoctors({ department_id: selectedDept || undefined, search: search || undefined }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-slate-900">Find Specialists & Doctors</h1>
        <p className="text-xs text-slate-500">Book instant OPD appointments with certified medical consultants</p>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search by doctor name or specialization..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="bg-white text-slate-800 border rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-sky-500"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {/* Doctor Grid */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">Loading specialist doctors...</div>
      ) : doctors.length === 0 ? (
        <div className="py-12 text-center text-slate-500">No doctors match your criteria.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {doctors.map((doc) => (
            <Card key={doc.id} hover className="flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-start gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-lg shrink-0">
                    <Stethoscope className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{doc.full_name}</h3>
                    <p className="text-xs text-sky-600 font-semibold">{doc.specialization}</p>
                    <p className="text-xs text-slate-500">{doc.department_name}</p>
                  </div>
                </div>

                <div className="space-y-1 text-xs text-slate-600 border-t pt-2.5">
                  <div className="flex items-center gap-1.5"><Award className="w-3.5 h-3.5 text-amber-500" /> {doc.qualification} • {doc.experience_years} yrs exp</div>
                  <div className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-400" /> {doc.location}</div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Fee</span>
                  <span className="text-sm font-bold text-slate-900">{formatCurrency(doc.consultation_fee)}</span>
                </div>
                <Button size="sm" onClick={() => navigate(`/patient/appointments/book?doctor_id=${doc.id}`)}>
                  Book Slot
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
