import React, { useState, useEffect } from 'react'
import {
  Users,
  Search,
  Filter,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  UserX,
  AlertTriangle,
  Clock,
  Calendar,
  Lock,
  LogIn,
  LogOut,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Activity,
  Globe,
  Smartphone,
  Laptop,
} from 'lucide-react'
import { adminService } from '@/services/admin'
import { AdminUser, LoginActivityItem } from '@/types'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'

const ROLE_OPTIONS = ['ALL', 'PATIENT', 'DOCTOR', 'ADMIN', 'FRONT_DESK', 'PENDING_DOCTOR', 'PENDING_FRONT_DESK']
const STATUS_OPTIONS = [
  { label: 'All Statuses', value: 'ALL' },
  { label: 'Active Only', value: 'ACTIVE' },
  { label: 'Inactive Only', value: 'INACTIVE' },
]

const ACTIVITY_EVENT_OPTIONS = [
  { label: 'All Security Events', value: 'ALL' },
  { label: 'Successful Logins', value: 'LOGIN_SUCCESS' },
  { label: 'Failed Logins', value: 'LOGIN_FAILED' },
  { label: 'Logouts', value: 'LOGOUT' },
]

export const AdminUsers: React.FC = () => {
  const { user: currentUser } = useAuth()
  const { showToast } = useToast()

  // Active Tab: 'users' | 'activity'
  const [activeTab, setActiveTab] = useState<'users' | 'activity'>('users')

  // Users State
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersTotal, setUsersTotal] = useState(0)
  const [usersPage, setUsersPage] = useState(1)
  const [usersPageSize] = useState(15)
  const [usersLoading, setUsersLoading] = useState(true)
  const [usersSearch, setUsersSearch] = useState('')
  const [selectedRole, setSelectedRole] = useState('ALL')
  const [selectedStatus, setSelectedStatus] = useState('ALL')

  // Status Modal State
  const [statusModalUser, setStatusModalUser] = useState<AdminUser | null>(null)
  const [statusReason, setStatusReason] = useState('')
  const [isSubmittingStatus, setIsSubmittingStatus] = useState(false)

  // Login Activity State
  const [activity, setActivity] = useState<LoginActivityItem[]>([])
  const [activityTotal, setActivityTotal] = useState(0)
  const [activityPage, setActivityPage] = useState(1)
  const [activityPageSize] = useState(20)
  const [activityLoading, setActivityLoading] = useState(false)
  const [activitySearch, setActivitySearch] = useState('')
  const [activityEventFilter, setActivityEventFilter] = useState('ALL')

  // Fetch Users
  const fetchUsers = async () => {
    setUsersLoading(true)
    try {
      const is_active =
        selectedStatus === 'ACTIVE' ? true : selectedStatus === 'INACTIVE' ? false : undefined
      const role = selectedRole === 'ALL' ? undefined : selectedRole
      const search = usersSearch.trim() || undefined

      const data = await adminService.getUsers({
        search,
        role,
        is_active,
        page: usersPage,
        page_size: usersPageSize,
      })

      setUsers(data.users || [])
      setUsersTotal(data.total || 0)
    } catch (err: any) {
      showToast(err?.response?.data?.detail || err?.message || 'Failed to load user directory', 'error')
    } finally {
      setUsersLoading(false)
    }
  }

  // Fetch Login Activity
  const fetchActivity = async () => {
    setActivityLoading(true)
    try {
      const event_type = activityEventFilter === 'ALL' ? undefined : activityEventFilter
      const search = activitySearch.trim() || undefined

      const data = await adminService.getLoginActivity({
        search,
        event_type,
        page: activityPage,
        page_size: activityPageSize,
      })

      setActivity(data.items || [])
      setActivityTotal(data.total || 0)
    } catch (err: any) {
      showToast(err?.response?.data?.detail || err?.message || 'Failed to load login activity', 'error')
    } finally {
      setActivityLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [usersPage, selectedRole, selectedStatus])

  useEffect(() => {
    if (activeTab === 'activity') {
      fetchActivity()
    }
  }, [activeTab, activityPage, activityEventFilter])

  // Handle Search Submissions
  const handleUserSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setUsersPage(1)
    fetchUsers()
  }

  const handleActivitySearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setActivityPage(1)
    fetchActivity()
  }

  // Handle Status Toggle
  const handleConfirmStatusToggle = async () => {
    if (!statusModalUser) return
    setIsSubmittingStatus(true)
    const newStatus = !statusModalUser.is_active

    try {
      const updated = await adminService.updateUserStatus(
        statusModalUser.id,
        newStatus,
        statusReason || undefined
      )

      showToast(
        `User ${updated.full_name} (${updated.email}) is now ${newStatus ? 'active' : 'deactivated'}.`,
        'success'
      )

      // Update in local state
      setUsers((prev) =>
        prev.map((u) => (u.id === updated.id ? { ...u, is_active: updated.is_active } : u))
      )
      setStatusModalUser(null)
      setStatusReason('')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to update user status'
      showToast(msg, 'error')
    } finally {
      setIsSubmittingStatus(false)
    }
  }

  const formatDateTime = (dateStr?: string | null) => {
    if (!dateStr) return '—'
    try {
      const d = new Date(dateStr)
      if (isNaN(d.getTime())) return '—'
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return '—'
    }
  }

  const formatRelativeTime = (dateStr?: string | null) => {
    if (!dateStr) return 'Never'
    try {
      const d = new Date(dateStr)
      if (isNaN(d.getTime())) return 'Never'
      const diffMs = Date.now() - d.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours}h ago`
      const diffDays = Math.floor(diffHours / 24)
      if (diffDays < 7) return `${diffDays}d ago`
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return 'Never'
    }
  }

  const getRoleBadge = (role: string) => {
    switch (role.toUpperCase()) {
      case 'ADMIN':
      case 'SUPER_ADMIN':
        return 'bg-purple-950/60 text-purple-300 border-purple-800/60'
      case 'DOCTOR':
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
      case 'FRONT_DESK':
        return 'bg-sky-950/60 text-sky-300 border-sky-800/60'
      case 'PATIENT':
        return 'bg-slate-800 text-slate-300 border-slate-700'
      default:
        return 'bg-amber-950/60 text-amber-300 border-amber-800/60'
    }
  }

  const getActivityBadge = (type: string) => {
    switch (type.toUpperCase()) {
      case 'LOGIN_SUCCESS':
        return {
          label: 'Login Success',
          badge: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60',
          icon: LogIn,
        }
      case 'LOGIN_FAILED':
        return {
          label: 'Login Failed',
          badge: 'bg-rose-950/60 text-rose-400 border-rose-800/60',
          icon: AlertTriangle,
        }
      case 'LOGOUT':
        return {
          label: 'Logged Out',
          badge: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
          icon: LogOut,
        }
      default:
        return {
          label: type,
          badge: 'bg-slate-800 text-slate-300 border-slate-700',
          icon: Activity,
        }
    }
  }

  const parseEventDetails = (detailsStr?: string | null) => {
    if (!detailsStr) return null
    try {
      return JSON.parse(detailsStr)
    } catch {
      return detailsStr
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <UserCheck className="w-7 h-7 text-sky-400" />
            User Management & Security Audit
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Centrally manage user accounts, monitor login authenticity, and inspect security activity logs.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'users'
                ? 'bg-sky-600 text-white shadow-sm shadow-sky-900'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            User Directory
            <span className="text-[10px] bg-slate-950/60 px-1.5 py-0.5 rounded-full border border-slate-700 font-mono">
              {usersTotal}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('activity')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
              activeTab === 'activity'
                ? 'bg-sky-600 text-white shadow-sm shadow-sky-900'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Login Activity
            {activityTotal > 0 && (
              <span className="text-[10px] bg-slate-950/60 px-1.5 py-0.5 rounded-full border border-slate-700 font-mono">
                {activityTotal}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* TAB 1: USER DIRECTORY */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* Controls Bar: Search & Filters */}
          <div className="bg-slate-800/80 p-4 rounded-2xl border border-slate-700 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
            <form onSubmit={handleUserSearchSubmit} className="flex-1 flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by full name, email, or phone..."
                  value={usersSearch}
                  onChange={(e) => setUsersSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl transition"
              >
                Search
              </button>
            </form>

            <div className="flex flex-wrap items-center gap-2">
              {/* Role Filter */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={selectedRole}
                  onChange={(e) => {
                    setSelectedRole(e.target.value)
                    setUsersPage(1)
                  }}
                  className="bg-transparent text-xs text-slate-200 focus:outline-none"
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r} className="bg-slate-800 text-white">
                      {r === 'ALL' ? 'All Roles' : r}
                    </option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5">
                <select
                  value={selectedStatus}
                  onChange={(e) => {
                    setSelectedStatus(e.target.value)
                    setUsersPage(1)
                  }}
                  className="bg-transparent text-xs text-slate-200 focus:outline-none"
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value} className="bg-slate-800 text-white">
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Refresh Button */}
              <button
                onClick={() => fetchUsers()}
                disabled={usersLoading}
                className="p-2 bg-slate-900 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 transition disabled:opacity-50"
                title="Refresh user directory"
              >
                <RefreshCw className={`w-4 h-4 ${usersLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-slate-800/90 rounded-2xl border border-slate-700 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-900/60 border-b border-slate-700/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Registered</th>
                    <th className="py-3 px-4">Last Login</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/60 text-slate-300">
                  {usersLoading ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
                        Loading registered users...
                      </td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <Users className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                        No users found matching current filters.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => {
                      const isSelf = u.id === currentUser?.id
                      return (
                        <tr key={u.id} className="hover:bg-slate-700/30 transition-colors">
                          {/* User info */}
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-slate-700/80 border border-slate-600 flex items-center justify-center font-bold text-xs text-white shrink-0">
                                {u.full_name?.charAt(0)?.toUpperCase() || 'U'}
                              </div>
                              <div className="overflow-hidden">
                                <div className="font-semibold text-white truncate flex items-center gap-1.5">
                                  <span>{u.full_name}</span>
                                  {isSelf && (
                                    <span className="text-[10px] bg-sky-950/80 text-sky-300 border border-sky-800 px-1.5 py-0.2 rounded font-medium">
                                      You
                                    </span>
                                  )}
                                </div>
                                <div className="text-[11px] text-slate-400 truncate">{u.email}</div>
                                {u.phone && <div className="text-[10px] text-slate-500">{u.phone}</div>}
                              </div>
                            </div>
                          </td>

                          {/* Role */}
                          <td className="py-3.5 px-4">
                            <span
                              className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-semibold border ${getRoleBadge(
                                u.role
                              )}`}
                            >
                              {u.role}
                            </span>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4">
                            {u.is_active ? (
                              <span className="inline-flex items-center gap-1.5 text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-2 py-0.5 rounded-full text-[10px] font-medium">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 text-rose-400 bg-rose-950/60 border border-rose-800/50 px-2 py-0.5 rounded-full text-[10px] font-medium">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                                Inactive
                              </span>
                            )}
                          </td>

                          {/* Registered date */}
                          <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                            {formatDateTime(u.created_at)}
                          </td>

                          {/* Last Login */}
                          <td className="py-3.5 px-4">
                            {u.last_login_at ? (
                              <div>
                                <span className="text-white text-[11px] font-medium">
                                  {formatRelativeTime(u.last_login_at)}
                                </span>
                                <div className="text-[10px] text-slate-500">
                                  {formatDateTime(u.last_login_at)}
                                </div>
                              </div>
                            ) : (
                              <span className="text-slate-500 text-[11px]">Never logged in</span>
                            )}
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={() => setStatusModalUser(u)}
                              disabled={isSelf && u.is_active}
                              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                                isSelf && u.is_active
                                  ? 'opacity-40 cursor-not-allowed bg-slate-800 text-slate-500 border-slate-700'
                                  : u.is_active
                                  ? 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border-rose-800/50'
                                  : 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border-emerald-800/50'
                              }`}
                              title={
                                isSelf && u.is_active
                                  ? 'You cannot deactivate your own admin account'
                                  : u.is_active
                                  ? 'Deactivate account'
                                  : 'Activate account'
                              }
                            >
                              {u.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="p-3 bg-slate-900/60 border-t border-slate-700 flex items-center justify-between text-xs text-slate-400">
              <div>
                Showing{' '}
                <span className="font-semibold text-white">
                  {users.length === 0 ? 0 : (usersPage - 1) * usersPageSize + 1}
                </span>{' '}
                to{' '}
                <span className="font-semibold text-white">
                  {Math.min(usersPage * usersPageSize, usersTotal)}
                </span>{' '}
                of <span className="font-semibold text-white">{usersTotal}</span> registered users
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setUsersPage((p) => Math.max(1, p - 1))}
                  disabled={usersPage <= 1 || usersLoading}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 disabled:opacity-40 transition flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Previous
                </button>
                <span className="px-2 font-mono text-slate-300">Page {usersPage}</span>
                <button
                  onClick={() => setUsersPage((p) => p + 1)}
                  disabled={usersPage * usersPageSize >= usersTotal || usersLoading}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 disabled:opacity-40 transition flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: LOGIN ACTIVITY */}
      {activeTab === 'activity' && (
        <div className="space-y-4">
          {/* Activity Filters */}
          <div className="bg-slate-800/80 p-4 rounded-2xl border border-slate-700 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
            <form onSubmit={handleActivitySearchSubmit} className="flex-1 flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search activity by email or IP address..."
                  value={activitySearch}
                  onChange={(e) => setActivitySearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl transition"
              >
                Search
              </button>
            </form>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={activityEventFilter}
                  onChange={(e) => {
                    setActivityEventFilter(e.target.value)
                    setActivityPage(1)
                  }}
                  className="bg-transparent text-xs text-slate-200 focus:outline-none"
                >
                  {ACTIVITY_EVENT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-slate-800 text-white">
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => fetchActivity()}
                disabled={activityLoading}
                className="p-2 bg-slate-900 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 transition disabled:opacity-50"
                title="Refresh login activity"
              >
                <RefreshCw className={`w-4 h-4 ${activityLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Activity Table */}
          <div className="bg-slate-800/90 rounded-2xl border border-slate-700 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-900/60 border-b border-slate-700/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">Event</th>
                    <th className="py-3 px-4">Account / Email</th>
                    <th className="py-3 px-4">IP Address</th>
                    <th className="py-3 px-4">Context / Method</th>
                    <th className="py-3 px-4">User-Agent</th>
                    <th className="py-3 px-4 text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/60 text-slate-300">
                  {activityLoading ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
                        Loading security activity audit trail...
                      </td>
                    </tr>
                  ) : activity.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <Activity className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                        No security activity records found.
                      </td>
                    </tr>
                  ) : (
                    activity.map((ev) => {
                      const badgeInfo = getActivityBadge(ev.event_type)
                      const Icon = badgeInfo.icon
                      const details = parseEventDetails(ev.details)
                      const method = typeof details === 'object' && details ? details.method : null

                      return (
                        <tr key={ev.id} className="hover:bg-slate-700/30 transition-colors">
                          {/* Event Type */}
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${badgeInfo.badge}`}
                            >
                              <Icon className="w-3.5 h-3.5" />
                              {badgeInfo.label}
                            </span>
                          </td>

                          {/* Account */}
                          <td className="py-3 px-4">
                            <div className="font-semibold text-white">{ev.user_email || 'Unknown'}</div>
                            {ev.user_id && (
                              <div className="text-[10px] text-slate-500 font-mono">
                                ID: {ev.user_id.slice(0, 12)}...
                              </div>
                            )}
                          </td>

                          {/* IP Address */}
                          <td className="py-3 px-4 font-mono text-[11px] text-slate-300">
                            {ev.ip_address || '—'}
                          </td>

                          {/* Context / Method */}
                          <td className="py-3 px-4">
                            {method ? (
                              <span className="text-[11px] bg-slate-900 border border-slate-700 px-2 py-0.5 rounded text-sky-300 font-mono">
                                {method}
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[11px]">—</span>
                            )}
                          </td>

                          {/* User Agent */}
                          <td className="py-3 px-4 text-slate-400 text-[11px] max-w-[220px] truncate" title={ev.user_agent || ''}>
                            {ev.user_agent || '—'}
                          </td>

                          {/* Timestamp */}
                          <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                            {formatDateTime(ev.created_at)}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="p-3 bg-slate-900/60 border-t border-slate-700 flex items-center justify-between text-xs text-slate-400">
              <div>
                Showing{' '}
                <span className="font-semibold text-white">
                  {activity.length === 0 ? 0 : (activityPage - 1) * activityPageSize + 1}
                </span>{' '}
                to{' '}
                <span className="font-semibold text-white">
                  {Math.min(activityPage * activityPageSize, activityTotal)}
                </span>{' '}
                of <span className="font-semibold text-white">{activityTotal}</span> security events
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActivityPage((p) => Math.max(1, p - 1))}
                  disabled={activityPage <= 1 || activityLoading}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 disabled:opacity-40 transition flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Previous
                </button>
                <span className="px-2 font-mono text-slate-300">Page {activityPage}</span>
                <button
                  onClick={() => setActivityPage((p) => p + 1)}
                  disabled={activityPage * activityPageSize >= activityTotal || activityLoading}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 disabled:opacity-40 transition flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STATUS TOGGLE CONFIRMATION MODAL */}
      {statusModalUser && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center border ${
                  statusModalUser.is_active
                    ? 'bg-rose-950/60 border-rose-800 text-rose-400'
                    : 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
                }`}
              >
                {statusModalUser.is_active ? (
                  <UserX className="w-5 h-5" />
                ) : (
                  <UserCheck className="w-5 h-5" />
                )}
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  {statusModalUser.is_active ? 'Deactivate User Account' : 'Activate User Account'}
                </h3>
                <p className="text-xs text-slate-400">
                  {statusModalUser.full_name} ({statusModalUser.email})
                </p>
              </div>
            </div>

            {statusModalUser.is_active ? (
              <div className="p-3 bg-amber-950/40 border border-amber-800/50 rounded-xl text-xs text-amber-300 space-y-1">
                <p className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 shrink-0" /> Warning: Deactivating Account
                </p>
                <p className="text-[11px] text-amber-400/90">
                  Deactivating this account will immediately revoke all of their active server-side sessions and reject future authentication attempts.
                </p>
              </div>
            ) : (
              <div className="p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-xl text-xs text-emerald-300">
                Activating this account will allow the user to log in and access system privileges granted by their role ({statusModalUser.role}).
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Administrative Reason / Audit Note (Optional)
              </label>
              <textarea
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                placeholder="Reason for changing this account's status..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none h-20"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  setStatusModalUser(null)
                  setStatusReason('')
                }}
                disabled={isSubmittingStatus}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmStatusToggle}
                disabled={isSubmittingStatus}
                className={`px-4 py-2 rounded-xl text-xs font-semibold text-white transition flex items-center gap-2 ${
                  statusModalUser.is_active
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : 'bg-emerald-600 hover:bg-emerald-500'
                } disabled:opacity-50`}
              >
                {isSubmittingStatus && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                {statusModalUser.is_active ? 'Confirm Deactivation' : 'Confirm Activation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminUsers
