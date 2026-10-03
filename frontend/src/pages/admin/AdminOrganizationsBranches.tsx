import React, { useState, useEffect } from 'react'
import {
  Building2,
  GitBranch,
  Plus,
  Users,
  MapPin,
  Clock,
  Phone,
  Mail,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Stethoscope,
  CalendarDays,
  IndianRupee,
  UserPlus,
  Hospital,
  AlertCircle
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import api from '@/services/api'
import { Organization, Branch } from '@/types'

export const AdminOrganizationsBranches: React.FC = () => {
  const { user } = useAuth()
  const { showToast } = useToast()

  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null)
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)

  // Modals
  const [showAddBranchModal, setShowAddBranchModal] = useState(false)
  const [showInviteStaffModal, setShowInviteStaffModal] = useState(false)
  const [selectedBranchForStaff, setSelectedBranchForStaff] = useState<Branch | null>(null)
  const [branchStaffList, setBranchStaffList] = useState<any[]>([])
  const [showStaffListModal, setShowStaffListModal] = useState(false)

  // Forms
  const [branchForm, setBranchForm] = useState({
    name: '',
    code: '',
    address: '',
    city: 'Bengaluru',
    state: 'Karnataka',
    pincode: '',
    phone: '',
    email: '',
    operating_hours: '08:00 AM - 08:00 PM (Mon-Sat)',
    is_active: true,
  })

  const [staffForm, setStaffForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    role: 'NURSE',
  })

  const [submitting, setSubmitting] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      // 1. Fetch organizations
      const orgRes = await api.get('/organizations')
      if (orgRes.data.success && orgRes.data.data.length > 0) {
        setOrganizations(orgRes.data.data)
        const currentOrg = orgRes.data.data[0]
        setSelectedOrg(currentOrg)
        setBranches(currentOrg.branches || [])
      } else {
        // Fallback: fetch scoped branches directly
        const bRes = await api.get('/branches')
        if (bRes.data.success) {
          setBranches(bRes.data.data)
        }
      }
    } catch (err: any) {
      // If user is branch-isolated, fetch branches directly
      try {
        const bRes = await api.get('/branches')
        if (bRes.data.success) {
          setBranches(bRes.data.data)
        }
      } catch (innerErr: any) {
        showToast(err?.response?.data?.detail || 'Failed to load organization details', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedOrg) {
      showToast('No organization selected to attach branch', 'error')
      return
    }

    setSubmitting(true)
    try {
      const res = await api.post(`/organizations/${selectedOrg.id}/branches`, branchForm)
      if (res.data.success) {
        showToast(`Branch '${branchForm.name}' created and clinic tenant provisioned!`, 'success')
        setShowAddBranchModal(false)
        setBranchForm({
          name: '',
          code: '',
          address: '',
          city: 'Bengaluru',
          state: 'Karnataka',
          pincode: '',
          phone: '',
          email: '',
          operating_hours: '08:00 AM - 08:00 PM (Mon-Sat)',
          is_active: true,
        })
        fetchData()
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to create branch', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleInviteStaff = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedBranchForStaff) return

    setSubmitting(true)
    try {
      const res = await api.post(`/branches/${selectedBranchForStaff.id}/staff`, staffForm)
      if (res.data.success) {
        showToast(`Staff member '${staffForm.full_name}' successfully provisioned!`, 'success')
        setShowInviteStaffModal(false)
        setStaffForm({
          full_name: '',
          email: '',
          phone: '',
          role: 'NURSE',
        })
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to provision staff', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleViewBranchStaff = async (branch: Branch) => {
    setSelectedBranchForStaff(branch)
    try {
      const res = await api.get(`/branches/${branch.id}/staff`)
      if (res.data.success) {
        setBranchStaffList(res.data.data)
        setShowStaffListModal(true)
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Could not fetch branch staff', 'error')
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 p-6 rounded-2xl border border-indigo-900/40 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Building2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  {selectedOrg ? selectedOrg.name : 'Multi-Branch Operations'}
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {selectedOrg ? `Code: ${selectedOrg.code}` : 'Healthcare Network'}
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                Enterprise multi-tenant hierarchy: Organization → Isolated Branches → Departments → Staff & Patients
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {['SUPER_ADMIN', 'ORGANIZATION_ADMIN', 'ADMIN'].includes(user?.role || '') && (
              <button
                onClick={() => setShowAddBranchModal(true)}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                Add New Branch
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Scope and Isolation Notice */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            <strong className="text-slate-200">Tenant & Branch Isolation Active:</strong> Regular Branch Admins are strictly scoped to their assigned physical facility. Super Admins & Organization Admins have enterprise oversight.
          </span>
        </div>
        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          Your Role: {user?.role}
        </span>
      </div>

      {/* Branches List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-indigo-400" />
            Operational Branches ({branches.length})
          </h2>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 bg-slate-900 rounded-2xl border border-slate-800">
            Loading branches and operational network...
          </div>
        ) : branches.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-900 rounded-2xl border border-slate-800 space-y-3">
            <AlertCircle className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-base text-slate-300">No branches registered yet.</p>
            <p className="text-xs text-slate-500">Create your first branch above to auto-provision a dedicated ClinicCare facility.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {branches.map((b) => (
              <div
                key={b.id}
                className="bg-slate-900 border border-slate-800 hover:border-indigo-500/40 rounded-2xl p-5 shadow-lg flex flex-col justify-between transition-all"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-bold text-white">{b.name}</h3>
                      <span className="text-xs font-mono font-medium text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900/50">
                        {b.code}
                      </span>
                    </div>
                    {b.is_active ? (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded-full border border-emerald-800/40">
                        <CheckCircle2 className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-950/50 px-2 py-0.5 rounded-full border border-rose-800/40">
                        <XCircle className="w-3 h-3" /> Inactive
                      </span>
                    )}
                  </div>

                  <div className="mt-4 space-y-2 text-xs text-slate-300">
                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                      <span className="truncate">{b.address || `${b.city}, ${b.state}`}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Clock className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                      <span>{b.operating_hours}</span>
                    </div>
                    {b.phone && (
                      <div className="flex items-center gap-2 text-slate-400">
                        <Phone className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                        <span>{b.phone}</span>
                      </div>
                    )}
                  </div>

                  {/* Branch KPI Quick Stats */}
                  <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-center">
                    <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800/50">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 flex items-center justify-center gap-1">
                        <Stethoscope className="w-3 h-3 text-sky-400" /> Doctors
                      </div>
                      <div className="text-sm font-bold text-white mt-0.5">{b.stats?.total_doctors ?? 0}</div>
                    </div>
                    <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800/50">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 flex items-center justify-center gap-1">
                        <CalendarDays className="w-3 h-3 text-indigo-400" /> Appts
                      </div>
                      <div className="text-sm font-bold text-white mt-0.5">{b.stats?.total_appointments ?? 0}</div>
                    </div>
                    <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800/50">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 flex items-center justify-center gap-1">
                        <Users className="w-3 h-3 text-emerald-400" /> Patients
                      </div>
                      <div className="text-sm font-bold text-white mt-0.5">{b.stats?.total_patients ?? 0}</div>
                    </div>
                    <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800/50">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 flex items-center justify-center gap-1">
                        <IndianRupee className="w-3 h-3 text-amber-400" /> Revenue
                      </div>
                      <div className="text-sm font-bold text-emerald-400 mt-0.5">
                        ₹{(b.stats?.total_revenue_inr ?? 0).toLocaleString('en-IN')}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleViewBranchStaff(b)}
                    className="flex-1 py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Users className="w-3.5 h-3.5 text-indigo-400" />
                    Staff Directory
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBranchForStaff(b)
                      setShowInviteStaffModal(true)
                    }}
                    className="py-1.5 px-3 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    Add Staff
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Branch Modal */}
      {showAddBranchModal && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Hospital className="w-5 h-5 text-indigo-400" />
                Add Operational Branch
              </h3>
              <button
                onClick={() => setShowAddBranchModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateBranch} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Branch Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Koramangala OPD Center"
                    value={branchForm.name}
                    onChange={(e) => setBranchForm({ ...branchForm, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Branch Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. KOR-01"
                    value={branchForm.code}
                    onChange={(e) => setBranchForm({ ...branchForm, code: e.target.value.toUpperCase() })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono uppercase focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Physical Address</label>
                <input
                  type="text"
                  placeholder="Street / Landmark / Building"
                  value={branchForm.address}
                  onChange={(e) => setBranchForm({ ...branchForm, address: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-slate-400 block mb-1">City</label>
                  <input
                    type="text"
                    value={branchForm.city}
                    onChange={(e) => setBranchForm({ ...branchForm, city: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">State</label>
                  <input
                    type="text"
                    value={branchForm.state}
                    onChange={(e) => setBranchForm({ ...branchForm, state: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Pincode</label>
                  <input
                    type="text"
                    placeholder="560034"
                    value={branchForm.pincode}
                    onChange={(e) => setBranchForm({ ...branchForm, pincode: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Phone</label>
                  <input
                    type="text"
                    placeholder="+91 99887 76655"
                    value={branchForm.phone}
                    onChange={(e) => setBranchForm({ ...branchForm, phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Email</label>
                  <input
                    type="email"
                    placeholder="branch@hospital.com"
                    value={branchForm.email}
                    onChange={(e) => setBranchForm({ ...branchForm, email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Operating Hours</label>
                <input
                  type="text"
                  value={branchForm.operating_hours}
                  onChange={(e) => setBranchForm({ ...branchForm, operating_hours: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddBranchModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Provision Branch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Staff Modal */}
      {showInviteStaffModal && selectedBranchForStaff && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-indigo-400" />
                  Assign Branch Staff
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">Facility: {selectedBranchForStaff.name}</p>
              </div>
              <button
                onClick={() => setShowInviteStaffModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleInviteStaff} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sister Priya Sharma"
                  value={staffForm.full_name}
                  onChange={(e) => setStaffForm({ ...staffForm, full_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Official Email *</label>
                <input
                  type="email"
                  required
                  placeholder="staff@hospital.com"
                  value={staffForm.email}
                  onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Contact Phone</label>
                <input
                  type="text"
                  placeholder="+91 98765 43210"
                  value={staffForm.phone}
                  onChange={(e) => setStaffForm({ ...staffForm, phone: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Role / Designation *</label>
                <select
                  value={staffForm.role}
                  onChange={(e) => setStaffForm({ ...staffForm, role: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="BRANCH_ADMIN">Branch Administrator / Manager</option>
                  <option value="NURSE">Staff Nurse / Triage</option>
                  <option value="PHARMACIST">Hospital Pharmacist</option>
                  <option value="LAB_TECHNICIAN">Laboratory Technician</option>
                  <option value="RADIOLOGIST">Radiologist / Imaging</option>
                  <option value="ACCOUNTANT">Billing & Accountant</option>
                  <option value="AMBULANCE_COORDINATOR">Ambulance Fleet Coordinator</option>
                </select>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowInviteStaffModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : 'Authorize Staff'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Staff Directory Modal */}
      {showStaffListModal && selectedBranchForStaff && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-400" />
                  Staff Members: {selectedBranchForStaff.name}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">Isolated Branch Operations Team</p>
              </div>
              <button
                onClick={() => setShowStaffListModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2">
              {branchStaffList.length === 0 ? (
                <p className="text-center text-xs text-slate-500 py-6">No staff members assigned to this branch yet.</p>
              ) : (
                branchStaffList.map((member) => (
                  <div
                    key={member.id}
                    className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-white text-xs">{member.full_name}</div>
                      <div className="text-[11px] text-slate-400">{member.email}</div>
                    </div>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-800/50 text-indigo-300">
                      {member.role}
                    </span>
                  </div>
                ))
              )}
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setShowStaffListModal(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
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
