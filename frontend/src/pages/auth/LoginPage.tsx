import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Activity, Lock, Mail, ArrowRight, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react'

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)
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
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200/90 shadow-xl shadow-slate-900/5">
        <div className="text-center space-y-1.5">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 items-center justify-center text-white shadow-md shadow-sky-500/20 mb-2">
            <Activity className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">ClinicCare</h1>
          <p className="text-xs font-semibold text-sky-700 tracking-wide">Healthcare Management Platform</p>
          <p className="text-[11px] text-slate-400">Sign in to access clinical services and account portal</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <Input
            label="Email Address"
            type="email"
            placeholder="name@hospital.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4 text-slate-400" />}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4 text-slate-400" />}
            required
          />

          <Button
            type="submit"
            className="w-full shadow-md shadow-sky-500/10"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Sign In
          </Button>
        </form>

        <div className="text-center text-xs text-slate-500 pt-1">
          Don't have an account?{' '}
          <Link to="/register" className="font-bold text-sky-600 hover:text-sky-700 underline decoration-sky-300 underline-offset-4">
            Register as Patient
          </Link>
        </div>

        {/* Collapsible Demo Role Selector */}
        <div className="pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={() => setShowDemoAccounts(!showDemoAccounts)}
            className="w-full flex items-center justify-between py-2 text-[11px] font-semibold text-slate-400 hover:text-slate-600 transition"
          >
            <span>Demo Test Accounts</span>
            {showDemoAccounts ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDemoAccounts && (
            <div className="mt-2 p-3 bg-slate-50 rounded-2xl border border-slate-200/70 space-y-2 animate-in fade-in duration-200">
              <p className="text-[10px] text-slate-500 text-center font-medium">Click to populate demo role credentials:</p>
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
