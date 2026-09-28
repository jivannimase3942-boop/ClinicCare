import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import { authService } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  Activity,
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  ShieldCheck,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react'

export const PatientRegisterPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1)
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    gender: 'male',
    blood_group: 'O+',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [otp, setOtp] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSendingOtp, setIsSendingOtp] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)

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

  // Step 1 -> Step 2
  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.full_name.trim()) {
      showToast('Please enter your full legal name', 'error')
      return
    }
    if (!formData.phone.trim()) {
      showToast('Please enter your contact phone number', 'error')
      return
    }
    setCurrentStep(2)
  }

  // Step 2 -> Step 3: validate credentials and send OTP
  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email.trim()) {
      showToast('Please enter your email address', 'error')
      return
    }
    if (formData.password.length < 6) {
      showToast('Password must be at least 6 characters long', 'error')
      return
    }
    if (formData.password !== formData.confirm_password) {
      showToast('Passwords do not match', 'error')
      return
    }

    setIsSendingOtp(true)
    try {
      const res = await authService.sendRegistrationOtp(formData.email.trim(), formData.full_name.trim())
      showToast(res.message || `Verification code dispatched to ${formData.email}`, 'success')
      setCurrentStep(3)
      setResendCooldown(60)
    } catch (err: any) {
      showToast(err.message || 'Failed to dispatch verification code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  const handleResendOtp = async () => {
    if (resendCooldown > 0 || isSendingOtp) return
    setIsSendingOtp(true)
    try {
      const res = await authService.sendRegistrationOtp(formData.email.trim(), formData.full_name.trim())
      showToast(res.message || 'New verification code dispatched', 'success')
      setResendCooldown(60)
    } catch (err: any) {
      showToast(err.message || 'Failed to resend code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  // Step 3 -> Step 4: verify OTP and finalize registration
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (otp.length < 6) {
      showToast('Please enter the 6-digit verification code', 'error')
      return
    }

    setIsLoading(true)
    try {
      await register({
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.full_name.trim(),
        phone: formData.phone.trim(),
        gender: formData.gender,
        blood_group: formData.blood_group,
        role: 'PATIENT',
        otp: otp.trim(),
      })
      setCurrentStep(4)
      showToast('Patient account created successfully!', 'success')
    } catch (err: any) {
      showToast(err.message || 'Verification failed. Please check the code.', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-900/5 space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-1">
            <Activity className="w-7 h-7 stroke-[2.5]" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Create Patient Account</h1>
          <p className="text-xs text-slate-500">
            {currentStep === 1 && 'Step 1 of 3: Personal Information'}
            {currentStep === 2 && 'Step 2 of 3: Security & Credentials'}
            {currentStep === 3 && 'Step 3 of 3: Email OTP Verification'}
            {currentStep === 4 && 'Account Verified & Activated'}
          </p>
        </div>

        {/* Step Indicator */}
        {currentStep < 4 && (
          <div className="flex items-center justify-center gap-2">
            {[1, 2, 3].map((stepNum) => (
              <div
                key={stepNum}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  currentStep === stepNum
                    ? 'w-10 bg-sky-600'
                    : currentStep > stepNum
                    ? 'w-6 bg-emerald-500'
                    : 'w-6 bg-slate-200'
                }`}
              />
            ))}
          </div>
        )}

        {/* Step 1: Personal Details */}
        {currentStep === 1 && (
          <form onSubmit={handleStep1Submit} className="space-y-4">
            <Input
              label="Full Name (Legal Name)"
              name="full_name"
              placeholder="e.g. Eleanor Vance"
              value={formData.full_name}
              onChange={handleChange}
              leftIcon={<User className="w-4 h-4 text-slate-400" />}
              required
            />

            <Input
              label="Contact Phone Number"
              name="phone"
              type="tel"
              placeholder="+1 (555) 019-2834"
              value={formData.phone}
              onChange={handleChange}
              leftIcon={<Phone className="w-4 h-4 text-slate-400" />}
              required
            />

            <div className="grid grid-cols-2 gap-3">
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

            <Button
              type="submit"
              className="w-full font-semibold shadow-md shadow-sky-500/10"
              size="lg"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue to Credentials
            </Button>
          </form>
        )}

        {/* Step 2: Email & Password */}
        {currentStep === 2 && (
          <form onSubmit={handleStep2Submit} className="space-y-4">
            <Input
              label="Email Address (Used for verification & login)"
              name="email"
              type="email"
              placeholder="eleanor@example.com"
              value={formData.email}
              onChange={handleChange}
              leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
              required
            />

            <Input
              label="Password (min 6 characters)"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              leftIcon={<Lock className="w-4 h-4 text-slate-400" />}
              required
              minLength={6}
            />

            <Input
              label="Confirm Password"
              name="confirm_password"
              type="password"
              placeholder="••••••••"
              value={formData.confirm_password}
              onChange={handleChange}
              leftIcon={<Lock className="w-4 h-4 text-slate-400" />}
              required
              minLength={6}
            />

            <div className="flex gap-2.5 pt-1">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCurrentStep(1)}
                className="w-1/3 text-xs"
              >
                <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
              </Button>
              <Button
                type="submit"
                className="w-2/3 font-semibold shadow-md shadow-sky-500/10"
                size="lg"
                isLoading={isSendingOtp}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Send Verification Code
              </Button>
            </div>
          </form>
        )}

        {/* Step 3: OTP Verification */}
        {currentStep === 3 && (
          <form onSubmit={handleVerifyOtp} className="space-y-5">
            <div className="bg-sky-50 border border-sky-100 rounded-2xl p-4 text-center space-y-1">
              <p className="text-xs font-semibold text-slate-600">Verification code dispatched to:</p>
              <p className="text-sm font-bold text-sky-800 font-mono">{formData.email}</p>
              <p className="text-[11px] text-slate-400">Code is valid for 10 minutes</p>
            </div>

            <div className="space-y-1.5 text-center">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Enter 6-Digit Code
              </label>
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

            <Button
              type="submit"
              className="w-full font-semibold shadow-md shadow-sky-500/10"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ShieldCheck className="w-4 h-4" />}
            >
              Verify Email & Create Account
            </Button>

            <div className="flex items-center justify-between text-xs pt-1">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="text-slate-500 hover:text-slate-800 font-semibold inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Change email
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resendCooldown > 0 || isSendingOtp}
                className={`font-semibold inline-flex items-center gap-1 ${
                  resendCooldown > 0
                    ? 'text-slate-400 cursor-not-allowed'
                    : 'text-sky-600 hover:text-sky-700'
                }`}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSendingOtp ? 'animate-spin' : ''}`} />
                {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend code'}
              </button>
            </div>
          </form>
        )}

        {/* Step 4: Account Created Success */}
        {currentStep === 4 && (
          <div className="text-center space-y-4 py-4">
            <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Account Created Successfully</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Your email identity has been verified and your patient portal profile is active.
              </p>
            </div>

            <Button
              type="button"
              className="w-full font-semibold"
              size="lg"
              onClick={() => navigate('/patient/dashboard', { replace: true })}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue to Patient Dashboard
            </Button>
          </div>
        )}

        <div className="text-center text-xs text-slate-500 pt-1 border-t border-slate-100">
          Already have an account?{' '}
          <Link to="/login" className="font-bold text-sky-600 hover:text-sky-700 underline decoration-sky-300 underline-offset-4">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  )
}
