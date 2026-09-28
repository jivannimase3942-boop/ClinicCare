import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { authService } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  Activity,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  KeyRound,
  RefreshCw,
} from 'lucide-react'

export const LoginPage: React.FC = () => {
  const [authMode, setAuthMode] = useState<'password' | 'otp'>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [isSendingOtp, setIsSendingOtp] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)

  const { login, loginWithOtp } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  const redirectUserByRole = (role: string) => {
    if (role === 'ADMIN') {
      navigate('/admin/dashboard', { replace: true })
    } else if (role === 'FRONT_DESK') {
      navigate('/frontdesk/dashboard', { replace: true })
    } else if (role === 'DOCTOR') {
      navigate('/doctor/dashboard', { replace: true })
    } else if (role === 'PENDING_DOCTOR' || role === 'PENDING_FRONT_DESK') {
      showToast('Account is pending verification by hospital administration', 'info')
      navigate('/login', { replace: true })
    } else {
      const from = (location.state as any)?.from?.pathname
      const dest = (!from || from === '/login' || from === '/') ? '/patient/dashboard' : from
      navigate(dest, { replace: true })
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return
    setIsLoading(true)
    try {
      const user = await login({ email, password })
      redirectUserByRole(user.role)
    } catch {
      // Handled by toast in AuthContext
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendLoginOtp = async () => {
    if (!email.trim()) {
      showToast('Please enter your email address first', 'error')
      return
    }
    setIsSendingOtp(true)
    try {
      const res = await authService.sendLoginOtp(email.trim())
      showToast(res.message || 'Login code sent to your email', 'success')
      setOtpSent(true)
    } catch (err: any) {
      showToast(err.message || 'Failed to send login code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !otp) return
    setIsLoading(true)
    try {
      const user = await loginWithOtp(email.trim(), otp.trim())
      redirectUserByRole(user.role)
    } catch {
      // Handled by toast in AuthContext
    } finally {
      setIsLoading(false)
    }
  }

  const fillDemo = (role: 'patient' | 'doctor' | 'admin' | 'frontdesk') => {
    setAuthMode('password')
    if (role === 'patient') {
      setEmail('patient@hospital.com')
      setPassword('Patient@123')
    } else if (role === 'doctor') {
      setEmail('dr.sharma@hospital.com')
      setPassword('Doctor@123')
    } else if (role === 'admin') {
      setEmail('admin@hospital.com')
      setPassword('Admin@123')
    } else if (role === 'frontdesk') {
      setEmail('frontdesk@hospital.com')
      setPassword('FrontDesk@123')
    }
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-900/5">
        {/* Brand Header */}
        <div className="text-center space-y-1.5">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-1">
            <Activity className="w-7 h-7 stroke-[2.5]" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">ClinicCare</h1>
          <p className="text-xs font-bold text-sky-700 uppercase tracking-wider">Secure Healthcare Access</p>
          <p className="text-xs text-slate-400">Sign in to access your role-specific dashboard</p>
        </div>

        {/* Tab Selector: Password vs Email OTP */}
        <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl text-xs font-semibold text-slate-600">
          <button
            type="button"
            onClick={() => {
              setAuthMode('password')
              setOtpSent(false)
            }}
            className={`py-2 rounded-lg transition ${
              authMode === 'password'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'hover:text-slate-900'
            }`}
          >
            Password Sign In
          </button>
          <button
            type="button"
            onClick={() => setAuthMode('otp')}
            className={`py-2 rounded-lg transition ${
              authMode === 'otp'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'hover:text-slate-900'
            }`}
          >
            Sign in with OTP
          </button>
        </div>

        {/* Password Login Form */}
        {authMode === 'password' ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-4 pt-1">
            <Input
              label="Email Address"
              type="email"
              placeholder="name@hospital.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
              required
            />

            <div className="space-y-1">
              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  leftIcon={<Lock className="w-4 h-4 text-slate-400" />}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-8 text-slate-400 hover:text-slate-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full shadow-md shadow-sky-500/10 font-semibold"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In
            </Button>
          </form>
        ) : (
          /* Email OTP Login Form */
          <form onSubmit={handleOtpSubmit} className="space-y-4 pt-1">
            <Input
              label="Email Address"
              type="email"
              placeholder="name@hospital.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
              required
            />

            {!otpSent ? (
              <Button
                type="button"
                variant="outline"
                className="w-full font-semibold"
                size="lg"
                onClick={handleSendLoginOtp}
                isLoading={isSendingOtp}
                leftIcon={<KeyRound className="w-4 h-4 text-sky-600" />}
              >
                Send Login Code
              </Button>
            ) : (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-700">6-Digit Verification Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    className="w-full text-center text-xl font-bold tracking-widest py-2.5 px-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
                    autoFocus
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full font-semibold"
                  size="lg"
                  isLoading={isLoading}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Verify & Sign In
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    onClick={handleSendLoginOtp}
                    disabled={isSendingOtp}
                    className="text-xs text-sky-600 hover:text-sky-700 font-medium inline-flex items-center gap-1"
                  >
                    <RefreshCw className={`w-3 h-3 ${isSendingOtp ? 'animate-spin' : ''}`} /> Resend code
                  </button>
                </div>
              </div>
            )}
          </form>
        )}

        {/* Google OAuth Section (Gracefully handled) */}
        {googleClientId ? (
          <div className="space-y-3">
            <div className="relative flex items-center justify-center">
              <div className="border-t border-slate-200 w-full" />
              <span className="bg-white px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                or
              </span>
            </div>
            <div id="google-signin-btn-container" className="flex justify-center">
              {/* Google official button container if configured */}
            </div>
          </div>
        ) : null}

        {/* Registration Options Link */}
        <div className="text-center text-xs text-slate-500 pt-1 border-t border-slate-100">
          New to ClinicCare?{' '}
          <Link
            to="/register"
            className="font-bold text-sky-600 hover:text-sky-700 underline decoration-sky-300 underline-offset-4"
          >
            Create an account / Request Access
          </Link>
        </div>

        {/* Collapsible Demo Accounts (for verification) */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setShowDemoAccounts(!showDemoAccounts)}
            className="w-full flex items-center justify-between py-2 text-[11px] font-semibold text-slate-400 hover:text-slate-600 transition"
          >
            <span>Demo accounts (evaluation)</span>
            {showDemoAccounts ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDemoAccounts && (
            <div className="mt-2 p-3 bg-slate-50 rounded-2xl border border-slate-200/70 space-y-2">
              <p className="text-[10px] text-slate-500 text-center font-medium">Click to populate credentials:</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                <button
                  type="button"
                  onClick={() => fillDemo('patient')}
                  className="px-2 py-1.5 bg-white border border-slate-200 hover:border-sky-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-sky-600 transition shadow-xs"
                >
                  Patient
                </button>
                <button
                  type="button"
                  onClick={() => fillDemo('doctor')}
                  className="px-2 py-1.5 bg-white border border-slate-200 hover:border-teal-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-teal-600 transition shadow-xs"
                >
                  Doctor
                </button>
                <button
                  type="button"
                  onClick={() => fillDemo('frontdesk')}
                  className="px-2 py-1.5 bg-white border border-slate-200 hover:border-amber-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-amber-600 transition shadow-xs"
                >
                  Front Desk
                </button>
                <button
                  type="button"
                  onClick={() => fillDemo('admin')}
                  className="px-2 py-1.5 bg-white border border-slate-200 hover:border-indigo-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-indigo-600 transition shadow-xs"
                >
                  Admin
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span>Role-Based Access Control • End-to-End Encrypted Session</span>
        </div>
      </div>
    </div>
  )
}
