import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Activity, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react'

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as any)?.from?.pathname || '/patient/dashboard'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return
    setIsLoading(true)
    try {
      const user = await login({ email, password })
      if (user.role === 'ADMIN' || user.role === 'FRONT_DESK') {
        navigate('/admin/dashboard', { replace: true })
      } else if (user.role === 'DOCTOR') {
        navigate('/doctor/dashboard', { replace: true })
      } else {
        const dest = (!from || from === '/login' || from === '/') ? '/patient/dashboard' : from
        navigate(dest, { replace: true })
      }
    } catch {
      // Handled by toast in AuthContext
    } finally {
      setIsLoading(false)
    }
  }

  const fillDemo = (role: 'patient' | 'doctor' | 'admin' | 'frontdesk') => {
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
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-3xl border border-slate-200 shadow-xl">
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-2">
            <Activity className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Sign in to ClinicCare</h2>
          <p className="text-xs text-slate-500">Access your appointments, medical records, and AI triage</p>
        </div>

        {/* Demo Quick Logins */}
        <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80 space-y-2">
          <p className="text-[11px] font-bold text-slate-600 uppercase tracking-wider text-center">Quick Demo Logins</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            <button
              type="button"
              onClick={() => fillDemo('patient')}
              className="px-2 py-1.5 bg-white border border-slate-200 hover:border-sky-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-sky-600 transition text-center shadow-xs"
            >
              Patient
            </button>
            <button
              type="button"
              onClick={() => fillDemo('doctor')}
              className="px-2 py-1.5 bg-white border border-slate-200 hover:border-teal-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-teal-600 transition text-center shadow-xs"
            >
              Doctor
            </button>
            <button
              type="button"
              onClick={() => fillDemo('admin')}
              className="px-2 py-1.5 bg-white border border-slate-200 hover:border-indigo-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-indigo-600 transition text-center shadow-xs"
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => fillDemo('frontdesk')}
              className="px-2 py-1.5 bg-white border border-slate-200 hover:border-amber-400 rounded-xl text-xs font-semibold text-slate-700 hover:text-amber-600 transition text-center shadow-xs"
            >
              Front Desk
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="patient@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            required
          />

          <Button
            type="submit"
            className="w-full"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Sign In
          </Button>
        </form>

        <div className="text-center text-xs text-slate-500 space-y-2">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="font-bold text-sky-600 hover:text-sky-700">
              Register as Patient
            </Link>
          </p>
          <p className="flex items-center justify-center gap-1 text-[11px] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> End-to-End Encrypted Session
          </p>
        </div>
      </div>
    </div>
  )
}
