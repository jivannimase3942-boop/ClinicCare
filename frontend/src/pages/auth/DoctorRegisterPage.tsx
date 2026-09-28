import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useToast } from '@/context/ToastContext'
import { authService } from '@/services/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  Stethoscope,
  Lock,
  Mail,
  User,
  Phone,
  ArrowRight,
  ShieldCheck,
  ArrowLeft,
  RefreshCw,
  Clock,
  Briefcase,
  GraduationCap,
} from 'lucide-react'

export const DoctorRegisterPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1)
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    specialization: '',
    qualification: '',
    experience_years: 5,
    password: '',
    confirm_password: '',
  })
  const [otp, setOtp] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSendingOtp, setIsSendingOtp] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)

  const { showToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (resendCooldown > 0) {
      timer = setTimeout(() => setResendCooldown((prev) => prev - 1), 1000)
    }
    return () => clearTimeout(timer)
  }, [resendCooldown])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleStep1Submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.full_name.trim() || !formData.specialization.trim() || !formData.qualification.trim()) {
      showToast('Please provide your complete professional credentials', 'error')
      return
    }
    setCurrentStep(2)
  }

  const handleStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email.trim()) {
      showToast('Please enter your professional email address', 'error')
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
      showToast(res.message || `Verification code sent to ${formData.email}`, 'success')
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
      showToast('New verification code sent', 'success')
      setResendCooldown(60)
    } catch (err: any) {
      showToast(err.message || 'Failed to resend code', 'error')
    } finally {
      setIsSendingOtp(false)
    }
  }

  const handleVerifyAndSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (otp.length < 6) {
      showToast('Please enter the 6-digit verification code', 'error')
      return
    }

    setIsLoading(true)
    try {
      await authService.requestDoctorAccess({
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.full_name.trim(),
        phone: formData.phone.trim(),
        specialization: formData.specialization.trim(),
        qualification: formData.qualification.trim(),
        experience_years: Number(formData.experience_years) || 0,
        otp: otp.trim(),
      })
      setCurrentStep(4)
      showToast('Doctor access request submitted for administrative verification', 'success')
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
          <div className="inline-flex w-12 h-12 rounded-2xl bg-teal-100 text-teal-700 items-center justify-center shadow-xs mb-1">
            <Stethoscope className="w-7 h-7 stroke-[2.5]" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Physician Access Request</h1>
          <p className="text-xs text-slate-500">
            {currentStep === 1 && 'Step 1 of 3: Clinical & Professional Details'}
            {currentStep === 2 && 'Step 2 of 3: Professional Email & Password'}
            {currentStep === 3 && 'Step 3 of 3: Email OTP Verification'}
            {currentStep === 4 && 'Request Submitted for Administrative Review'}
          </p>
        </div>

        {/* Step 1: Professional Details */}
        {currentStep === 1 && (
          <form onSubmit={handleStep1Submit} className="space-y-4">
            <Input
              label="Full Name (with Dr. prefix)"
              name="full_name"
              placeholder="Dr. Sarah Jenkins"
              value={formData.full_name}
              onChange={handleChange}
              leftIcon={<User className="w-4 h-4 text-slate-400" />}
              required
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Primary Specialization"
                name="specialization"
                placeholder="Cardiology / Internal Med"
                value={formData.specialization}
                onChange={handleChange}
                leftIcon={<Briefcase className="w-4 h-4 text-slate-400" />}
                required
              />

              <Input
                label="Highest Qualification"
                name="qualification"
                placeholder="MD, FACC, MBBS"
                value={formData.qualification}
                onChange={handleChange}
                leftIcon={<GraduationCap className="w-4 h-4 text-slate-400" />}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Years of Experience"
                name="experience_years"
                type="number"
                min={0}
                max={60}
                value={formData.experience_years.toString()}
                onChange={handleChange}
                required
              />

              <Input
                label="Contact Phone"
                name="phone"
                type="tel"
                placeholder="+1 (555) 019-3388"
                value={formData.phone}
                onChange={handleChange}
                leftIcon={<Phone className="w-4 h-4 text-slate-400" />}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full font-semibold shadow-md shadow-teal-500/10"
              size="lg"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Continue to Credentials
            </Button>
          </form>
        )}

        {/* Step 2: Credentials */}
        {currentStep === 2 && (
          <form onSubmit={handleStep2Submit} className="space-y-4">
            <Input
              label="Professional / Hospital Email"
              name="email"
              type="email"
              placeholder="dr.jenkins@hospital.com"
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
                className="w-2/3 font-semibold shadow-md shadow-teal-500/10"
                size="lg"
                isLoading={isSendingOtp}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Send Verification Code
              </Button>
            </div>
          </form>
        )}

        {/* Step 3: OTP */}
        {currentStep === 3 && (
          <form onSubmit={handleVerifyAndSubmit} className="space-y-5">
            <div className="bg-teal-50 border border-teal-100 rounded-2xl p-4 text-center space-y-1">
              <p className="text-xs font-semibold text-slate-600">Verification code sent to professional email:</p>
              <p className="text-sm font-bold text-teal-800 font-mono">{formData.email}</p>
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
                className="w-full text-center text-2xl font-black tracking-widest py-3 px-4 border-2 border-slate-200 focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10 rounded-2xl outline-none font-mono transition"
                autoFocus
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full font-semibold shadow-md shadow-teal-500/10"
              size="lg"
              isLoading={isLoading}
              rightIcon={<ShieldCheck className="w-4 h-4" />}
            >
              Verify Email & Submit Request
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
                    : 'text-teal-600 hover:text-teal-700'
                }`}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSendingOtp ? 'animate-spin' : ''}`} />
                {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : 'Resend code'}
              </button>
            </div>
          </form>
        )}

        {/* Step 4: Submission Confirmation */}
        {currentStep === 4 && (
          <div className="text-center space-y-4 py-4">
            <div className="w-14 h-14 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto shadow-sm">
              <Clock className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-900">Request Submitted for Verification</h3>
              <p className="text-xs text-slate-600 leading-relaxed max-w-sm mx-auto">
                Your email has been verified. Your physician credentials and medical license information have been
                submitted to the hospital administration for review.
              </p>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500">
                You will receive clinical access once an administrator approves your account.
              </div>
            </div>

            <Button
              type="button"
              className="w-full font-semibold"
              size="lg"
              onClick={() => navigate('/login', { replace: true })}
            >
              Return to Sign In
            </Button>
          </div>
        )}

        <div className="text-center text-xs text-slate-500 pt-1 border-t border-slate-100">
          Already verified?{' '}
          <Link to="/login" className="font-bold text-teal-600 hover:text-teal-700 underline decoration-teal-300 underline-offset-4">
            Sign In to Doctor Portal
          </Link>
        </div>
      </div>
    </div>
  )
}
