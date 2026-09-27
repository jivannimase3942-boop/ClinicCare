import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorService } from '@/services/doctors'
import { adminService } from '@/services/admin'
import { useToast } from '@/context/ToastContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Building2, Plus } from 'lucide-react'

export const AdminDepartments: React.FC = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [isOpen, setIsOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const { data: departments = [], isLoading } = useQuery({
    queryKey: ['departments'],
    queryFn: () => doctorService.getDepartments(),
  })

  const mutation = useMutation({
    mutationFn: () => adminService.createDepartment({ name, description }),
    onSuccess: () => {
      showToast('Department created successfully', 'success')
      setName('')
      setDescription('')
      setIsOpen(false)
      queryClient.invalidateQueries({ queryKey: ['departments'] })
    },
    onError: (err: any) => showToast(err.message || 'Creation failed', 'error'),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Hospital Departments</h1>
          <p className="text-xs text-slate-400">Clinical wings and specialty departments</p>
        </div>
        <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsOpen(true)}>
          Add Department
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading departments...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((dept) => (
            <div key={dept.id} className="bg-slate-800/80 border border-slate-700 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">{dept.name}</h3>
                  <span className="text-[10px] text-emerald-400 font-semibold uppercase">Active Clinic</span>
                </div>
              </div>
              <p className="text-xs text-slate-400">{dept.description || 'Specialized clinical outpatient unit.'}</p>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Create Department">
        <div className="space-y-4">
          <Input label="Department Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Oncology" required />
          <Input label="Description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Cancer care and chemotherapy" />
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsOpen(false)}>Cancel</Button>
            <Button size="sm" isLoading={mutation.isPending} disabled={!name.trim()} onClick={() => mutation.mutate()}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
