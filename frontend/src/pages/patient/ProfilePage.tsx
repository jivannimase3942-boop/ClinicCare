import React, { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import api from '@/services/api'
import { Card, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  User,
  Mail,
  Phone,
  Lock,
  ShieldCheck,
  Laptop,
  LogOut,
  FileCheck2,
  Download,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  KeyRound,
} from 'lucide-react'

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth()
  const { showToast } = useToast()

  const [activeTab, setActiveTab] = useState<'profile' | 'sessions' | 'consents' | 'privacy'>('profile')

  // Password state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false)

  // Sessions state
  const [sessions, setSessions] = useState<any[]>([])
  const [loadingSessions, setLoadingSessions] = useState(false)

  // Consents state
  const [consents, setConsents] = useState<any[]>([])
  const [loadingConsents, setLoadingConsents] = useState(false)
  const [grantingConsent, setGrantingConsent] = useState(false)
  const [consentTypeToGrant, setConsentTypeToGrant] = useState('TELEMEDICINE_CONSENT')
  const [consentPurpose, setConsentPurpose] = useState('Virtual consultation and clinical video assessment')

  // Privacy requests state
  const [privacyRequests, setPrivacyRequests] = useState<any[]>([])
  const [exportingData, setExportingData] = useState(false)
  const [requestingDeletion, setRequestingDeletion] = useState(false)
  const [deletionReason, setDeletionReason] = useState('')

  // MFA state
  const [mfaStatus, setMfaStatus] = useState<any>({ is_enabled: false, method: 'EMAIL_OTP', configured: true })

  const fetchSessions = async () => {
    setLoadingSessions(true)
    try {
      const res = await api.get('/security/sessions')
      if (res.data.success) {
        setSessions(res.data.data)
      }
    } catch (err: any) {
      // Non-fatal if session table is empty
    } finally {
      setLoadingSessions(false)
    }
  }

  const fetchConsents = async () => {
    setLoadingConsents(true)
    try {
      const res = await api.get('/consents/my')
      if (res.data.success) {
        setConsents(res.data.data)
      }
    } catch (err: any) {
      // Non-fatal
    } finally {
      setLoadingConsents(false)
    }
  }

  const fetchPrivacy = async () => {
    try {
      const res = await api.get('/privacy/requests/my')
      if (res.data.success) {
        setPrivacyRequests(res.data.data)
      }
    } catch (err: any) {}
  }

  const fetchMfa = async () => {
    try {
      const res = await api.get('/security/mfa/status')
      if (res.data.success) {
        setMfaStatus(res.data.data)
      }
    } catch (err: any) {}
  }

  useEffect(() => {
    fetchSessions()
    fetchConsents()
    fetchPrivacy()
    fetchMfa()
  }, [])

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentPassword || !newPassword) return
    setIsUpdatingPassword(true)
    try {
      await api.post('/security/change-password', {
        old_password: currentPassword,
        new_password: newPassword,
      })
      showToast('Password updated successfully. Other sessions logged out.', 'success')
      setCurrentPassword('')
      setNewPassword('')
      fetchSessions()
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to update password', 'error')
    } finally {
      setIsUpdatingPassword(false)
    }
  }

  const handleLogoutCurrentSession = async () => {
    try {
      await api.post('/security/sessions/logout-current')
      showToast('Current session terminated', 'info')
      logout()
    } catch (err: any) {
      showToast('Failed to terminate session', 'error')
    }
  }

  const handleLogoutAllSessions = async () => {
    try {
      const res = await api.post('/security/sessions/logout-all')
      showToast(res.data.message || 'All sessions revoked', 'success')
      fetchSessions()
    } catch (err: any) {
      showToast('Failed to revoke sessions', 'error')
    }
  }

  const handleGrantConsent = async (e: React.FormEvent) => {
    e.preventDefault()
    setGrantingConsent(true)
    try {
      const res = await api.post('/consents', {
        consent_type: consentTypeToGrant,
        purpose: consentPurpose,
        source: 'PATIENT_PORTAL',
      })
      if (res.data.success) {
        showToast('Consent granted and securely recorded', 'success')
        fetchConsents()
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to record consent', 'error')
    } finally {
      setGrantingConsent(false)
    }
  }

  const handleWithdrawConsent = async (consentId: string) => {
    try {
      await api.post(`/consents/${consentId}/withdraw`, {
        reason: 'Withdrawn by patient from settings portal',
      })
      showToast('Consent withdrawn successfully', 'info')
      fetchConsents()
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Failed to withdraw consent', 'error')
    }
  }

  const handleRequestDataExport = async () => {
    setExportingData(true)
    try {
      const res = await api.post('/privacy/export-request', {
        request_type: 'DATA_EXPORT',
        reason: 'Patient self-service digital records export',
      })
      if (res.data.success) {
        showToast('Medical record export generated successfully', 'success')
        fetchPrivacy()
        // Offer download
        const payload = res.data.data.export_payload
        if (payload) {
          const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `ClinicCare_Patient_Export_${new Date().toISOString().split('T')[0]}.json`
          a.click()
        }
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Export request failed', 'error')
    } finally {
      setExportingData(false)
    }
  }

  const handleRequestDeletion = async (e: React.FormEvent) => {
    e.preventDefault()
    setRequestingDeletion(true)
    try {
      const res = await api.post('/privacy/deletion-request', {
        request_type: 'DATA_DELETION',
        reason: deletionReason || 'Patient requested account closure',
      })
      if (res.data.success) {
        showToast('Deletion request submitted for administrative review', 'warning')
        setDeletionReason('')
        fetchPrivacy()
      }
    } catch (err: any) {
      showToast(err?.response?.data?.detail || 'Deletion request failed', 'error')
    } finally {
      setRequestingDeletion(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Patient Profile, Privacy & Security</h1>
        <p className="text-xs text-slate-400 mt-1">
          Unified security portal: session isolation, statutory healthcare consents, and DPDPA privacy controls
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-2 overflow-x-auto pb-1 text-sm font-medium">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2 rounded-t-xl transition-colors cursor-pointer ${
            activeTab === 'profile'
              ? 'bg-slate-800 text-sky-400 border-b-2 border-sky-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Credentials & Profile
        </button>
        <button
          onClick={() => setActiveTab('sessions')}
          className={`px-4 py-2 rounded-t-xl transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'sessions'
              ? 'bg-slate-800 text-sky-400 border-b-2 border-sky-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Laptop className="w-4 h-4" />
          Active Sessions ({sessions.length})
        </button>
        <button
          onClick={() => setActiveTab('consents')}
          className={`px-4 py-2 rounded-t-xl transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'consents'
              ? 'bg-slate-800 text-sky-400 border-b-2 border-sky-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          Consents ({consents.filter((c) => c.status === 'GRANTED').length})
        </button>
        <button
          onClick={() => setActiveTab('privacy')}
          className={`px-4 py-2 rounded-t-xl transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'privacy'
              ? 'bg-slate-800 text-sky-400 border-b-2 border-sky-400 font-semibold'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Data Privacy & DSAR
        </button>
      </div>

      {/* Tab 1: Profile & Credentials */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Personal Identification</CardTitle>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Full Name" value={user?.full_name || ''} disabled leftIcon={<User className="w-4 h-4" />} />
              <Input label="Email Address" value={user?.email || ''} disabled leftIcon={<Mail className="w-4 h-4" />} />
              <Input label="Phone Number" value={user?.phone || 'Not provided'} disabled leftIcon={<Phone className="w-4 h-4" />} />
              <Input label="Role" value={user?.role || 'PATIENT'} disabled leftIcon={<ShieldCheck className="w-4 h-4" />} />
            </div>

            {/* MFA Status Badge */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <KeyRound className="w-4 h-4 text-emerald-400" />
                <span>Multi-Factor Security (MFA): <strong>Ready & Supported</strong></span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/50 text-emerald-400 text-[11px] font-semibold">
                Email OTP Ready
              </span>
            </div>
          </Card>

          <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Change Password</CardTitle>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <Input
                label="Current Password"
                type="password"
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                leftIcon={<Lock className="w-4 h-4" />}
                required
              />
              <Input
                label="New Password"
                type="password"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                leftIcon={<Lock className="w-4 h-4" />}
                required
                minLength={8}
              />
              <Button type="submit" isLoading={isUpdatingPassword} disabled={isUpdatingPassword}>
                Update Security Password
              </Button>
            </form>
          </Card>
        </div>
      )}

      {/* Tab 2: Active Sessions */}
      {activeTab === 'sessions' && (
        <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Logged-in Sessions</CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">
                Revoke any unfamiliar sessions or terminate access across all devices
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleLogoutCurrentSession}>
                <LogOut className="w-3.5 h-3.5 mr-1" /> Logout Current
              </Button>
              <Button variant="danger" size="sm" onClick={handleLogoutAllSessions}>
                Revoke All Sessions
              </Button>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            {loadingSessions ? (
              <p className="text-xs text-slate-500 py-4 text-center">Loading sessions...</p>
            ) : sessions.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No tracked session records found.</p>
            ) : (
              sessions.map((sess) => (
                <div
                  key={sess.id}
                  className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400">
                      <Laptop className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-semibold text-white flex items-center gap-2">
                        <span>{sess.user_agent ? sess.user_agent.slice(0, 45) : 'Web Client'}</span>
                        {sess.is_current && (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                            Current Device
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        IP: {sess.ip_address || '127.0.0.1'} • Last active:{' '}
                        {new Date(sess.last_activity_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Expires: {new Date(sess.expires_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Tab 3: Healthcare Consents */}
      {activeTab === 'consents' && (
        <div className="space-y-6">
          <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Grant Explicit Healthcare Consent</CardTitle>
            <form onSubmit={handleGrantConsent} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Consent Type *</label>
                  <select
                    value={consentTypeToGrant}
                    onChange={(e) => setConsentTypeToGrant(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="TELEMEDICINE_CONSENT">Telemedicine & Video Consultation Consent</option>
                    <option value="COMMUNICATION_CONSENT">WhatsApp & SMS Health Reminders Consent</option>
                    <option value="DATA_SHARING_CONSENT">Clinical Data Sharing with Consulting Specialists</option>
                    <option value="DOCUMENT_SHARING_CONSENT">Laboratory & Imaging Digital Report Delivery</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Specific Purpose *</label>
                  <input
                    type="text"
                    required
                    value={consentPurpose}
                    onChange={(e) => setConsentPurpose(e.target.value)}
                    placeholder="e.g. Remote cardiology consult"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" isLoading={grantingConsent} disabled={grantingConsent} size="sm">
                  Record Consent
                </Button>
              </div>
            </form>
          </Card>

          <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Consent History & Status</CardTitle>
            <div className="space-y-2.5">
              {loadingConsents ? (
                <p className="text-xs text-slate-500 py-4 text-center">Loading consents...</p>
              ) : consents.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No explicit consent records recorded yet.</p>
              ) : (
                consents.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{c.consent_type.replace(/_/g, ' ')}</span>
                        {c.status === 'GRANTED' ? (
                          <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                            <CheckCircle2 className="w-3 h-3" /> Active
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-[10px] font-bold text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">
                            <XCircle className="w-3 h-3" /> Withdrawn
                          </span>
                        )}
                      </div>
                      <p className="text-slate-400 mt-1">{c.purpose}</p>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Recorded on {new Date(c.granted_at).toLocaleDateString()} via {c.source}
                        {c.revoked_at && ` • Revoked on ${new Date(c.revoked_at).toLocaleDateString()}`}
                      </div>
                    </div>

                    {c.status === 'GRANTED' && (
                      <button
                        onClick={() => handleWithdrawConsent(c.id)}
                        className="px-2.5 py-1 rounded bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-[11px] font-semibold cursor-pointer transition-colors"
                      >
                        Withdraw
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Tab 4: Data Privacy & DSAR */}
      {activeTab === 'privacy' && (
        <div className="space-y-6">
          <Card className="space-y-4 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Digital Personal Data Protection & DSAR Requests</CardTitle>
            <p className="text-xs text-slate-400">
              Exercise your data rights under India's Digital Personal Data Protection Act (DPDPA) and global privacy standards.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {/* Export Box */}
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
                  <Download className="w-4 h-4" />
                  Request Full Data Export
                </div>
                <p className="text-xs text-slate-400">
                  Export your comprehensive medical timeline, vitals, prescriptions, consultation notes, and active consents in machine-readable JSON format.
                </p>
                <Button size="sm" onClick={handleRequestDataExport} isLoading={exportingData} disabled={exportingData}>
                  Generate & Download Export
                </Button>
              </div>

              {/* Deletion Box */}
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
                  <Trash2 className="w-4 h-4" />
                  Account & Data Deletion
                </div>
                <p className="text-xs text-slate-400">
                  Submit a formal deletion request. Clinical records are subject to statutory NMC retention requirements (3-5 years) and will be securely archived.
                </p>
                <form onSubmit={handleRequestDeletion} className="space-y-2">
                  <input
                    type="text"
                    placeholder="Reason for deletion request..."
                    value={deletionReason}
                    onChange={(e) => setDeletionReason(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-rose-500"
                  />
                  <Button variant="danger" size="sm" type="submit" isLoading={requestingDeletion} disabled={requestingDeletion}>
                    Submit Deletion Request
                  </Button>
                </form>
              </div>
            </div>

            {/* Retention Advisory Note */}
            <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-xl flex items-start gap-2 text-xs text-amber-300/90">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
              <div>
                <strong>Statutory Health Records Retention Notice:</strong>
                <p className="mt-0.5 text-[11px] text-amber-200/80">
                  In compliance with National Medical Commission (NMC) regulations and clinical establishment governance, core inpatient/outpatient medical histories must be legally retained for statutory compliance periods before complete electronic record purging.
                </p>
              </div>
            </div>
          </Card>

          {/* Privacy Request History */}
          <Card className="space-y-3 bg-slate-900 border-slate-800 text-slate-100">
            <CardTitle>Privacy Request History</CardTitle>
            <div className="space-y-2 text-xs">
              {privacyRequests.length === 0 ? (
                <p className="text-xs text-slate-500 py-3 text-center">No past privacy requests submitted.</p>
              ) : (
                privacyRequests.map((r) => (
                  <div key={r.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-white">{r.request_type.replace(/_/g, ' ')}</span>
                      <p className="text-slate-400 mt-0.5">{r.reason || 'Self-service request'}</p>
                      {r.retention_note && (
                        <p className="text-[10px] text-amber-400/80 mt-1 italic">{r.retention_note}</p>
                      )}
                    </div>
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-indigo-950/70 text-indigo-300 border border-indigo-800/50">
                      {r.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
