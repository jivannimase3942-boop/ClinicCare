import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { authService } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Activity, Lock, Mail, User, Phone, ArrowRight, ShieldCheck, KeyRound, ArrowLeft, RefreshCw } from 'lucide-react'

export const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    gender: 'male',
    blood_group: 'O+',
  })
  const [step, setStep] = useState<'details' | 'otp'>('details')
  const [otp, setOtp] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSendingOtp, setIsSendingOtp] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [devCode, setDevCode] = useState<string | null>(null)

  const { register } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (resendCooldown > 0) {
      timer = setTimeout(() => setResendCooldown((prev) => prev - 1), 1000)
    }
    return () => clearTimeout(timer)
  }, [resendCooldown])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email || !formData.password || !formData.full_name) {
      showToast('Please fill in all required fields', 'error')
      return
    }
    if (formData.password.length < 6) {
      showToast('Password must be at least 6 characters long', 'error')
      return
    }

    setIsSendingOtp(true)
    try {
      const res = await authService.sendRegistrationOtp(formData.email, formData.full_name)
      showToast(res.message || `Verification code sent to ${formData.email}`, 'success')
      if (res.dev_code) {
        setDevCode(res.dev_code)
      }
      setStep('otp')
      setResendCooldown(60)
    } catch (err: any) {
      showToast(err.message || 'Failed to send verification code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  const handleResendOtp = async () => {
    if (resendCooldown > 0) return
    setIsSendingOtp(true)
    try {
      const res = await authService.sendRegistrationOtp(formData.email, formData.full_name)
      showToast('New verification code sent!', 'success')
      if (res.dev_code) {
        setDevCode(res.dev_code)
      }
      setResendCooldown(60)
    } catch (err: any) {
      showToast(err.message || 'Failed to resend verification code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  const handleVerifyAndRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp.trim()) {
      showToast('Please enter the 6-digit verification code', 'error')
      return
    }

    setIsLoading(true)
    try {
      await register({
        ...formData,
        role: 'PATIENT',
        otp: otp.trim(),
      })
      showToast('Account created and verified successfully!', 'success')
      navigate('/patient/dashboard', { replace: true })
    } catch (err: any) {
      showToast(err.message || 'Verification failed. Please check the code.', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-6 bg-white p-8 rounded-3xl border border-slate-200 shadow-xl">
        <div className="text-center space-y-1.5">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-2">
            <Activity className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">
            {step === 'details' ? 'Create Patient Account' : 'Verify Email Address'}
          </h2>
          <p className="text-xs text-slate-500">
            {step === 'details'
              ? 'Join ClinicCare to book appointments and track medical records'
              : `Enter the 6-digit verification code sent to ${formData.email}`}
          </p>
        </div>

        {step === 'details' ? (
          <form onSubmit={handleRequestOtp} className="space-y-4">
            <Input
              label="Full Name"
              name="full_name"
              placeholder="John Doe"
              value={formData.full_name}
              onChange={handleChange}
              leftIcon={<User className="w-4 h-4" />}
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Email Address"
                name="email"
                type="email"
                placeholder="patient@example.com"
                value={formData.email}
                onChange={handleChange}
                leftIcon={<Mail className="w-4 h-4" />}
                required
              />

              <Input
                label="Phone Number"
                name="phone"
                type="tel"
                placeholder="+1 555-0199"
                value={formData.phone}
                onChange={handleChange}
                leftIcon={<Phone className="w-4 h-4" />}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Gender"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </Select>

              <Select
                label="Blood Group"
                name="blood_group"
                value={formData.blood_group}
                onChange={handleChange}
              >
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </Select>
            </div>

            <Input
              label="Password (min 6 characters)"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              leftIcon={<Lock className="w-4 h-4" />}
              required
              minLength={6}
            />

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isSendingOtp}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue to Email Verification
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerifyAndRegister} className="space-y-5">
            <div className="bg-sky-50 border border-sky-100 rounded-2xl p-4 text-center space-y-1">
              <p className="text-xs font-semibold text-sky-900">Verification code sent to:</p>
              <p className="text-sm font-bold text-sky-700 font-mono">{formData.email}</p>
              {devCode && (
                <div className="mt-2 py-1 px-2.5 bg-amber-50 border border-amber-200 rounded-lg inline-block text-[11px] text-amber-800 font-mono">
                  Test OTP: <strong>{devCode}</strong>
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider text-center">
                6-Digit Security OTP
              </label>
              <div className="relative">
                <input
                  type="text"
                  maxLength={6}
                  placeholder="123456"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full text-center text-2xl font-black tracking-widest py-3 px-4 border-2 border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 rounded-2xl outline-none font-mono transition"
                  autoFocus
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ShieldCheck className="w-4 h-4" />}
            >
              Verify & Complete Registration
            </Button>

            <div className="flex items-center justify-between text-xs pt-1">
              <button
                type="button"
                onClick={() => setStep('details')}
                className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-800 font-semibold"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to details
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resendCooldown > 0 || isSendingOtp}
                className={`inline-flex items-center gap-1 font-semibold ${
                  resendCooldown > 0
                    ? 'text-slate-400 cursor-not-allowed'
                    : 'text-sky-600 hover:text-sky-700'
                }`}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSendingOtp ? 'animate-spin' : ''}`} />
                {resendCooldown > 0 ? `Resend code (${resendCooldown}s)` : 'Resend code'}
              </button>
            </div>
          </form>
        )}

        <div className="text-center text-xs text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="font-bold text-sky-600 hover:text-sky-700">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  )
}
