import React from 'react'
import { Activity, ShieldCheck, Heart, Phone, Mail, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-sm border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-teal-400 flex items-center justify-center text-white font-bold">
                <Activity className="w-4 h-4" />
              </div>
              <span className="text-lg font-black text-white tracking-tight">ClinicCare</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Secure, unified clinical orchestration platform connecting healthcare teams and patients.
            </p>
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <ShieldCheck className="w-4 h-4" /> Role-Isolated Clinical Security
            </div>
          </div>

          {/* Quick Access */}
          <div>
            <h4 className="text-white font-semibold text-xs uppercase tracking-wider mb-3">Portal Access</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/login" className="hover:text-white transition">
                  Sign In to Account
                </Link>
              </li>
              <li>
                <Link to="/register/patient" className="hover:text-white transition">
                  Patient Registration
                </Link>
              </li>
              <li>
                <Link to="/register/doctor" className="hover:text-white transition">
                  Doctor Access Request
                </Link>
              </li>
              <li>
                <Link to="/register/frontdesk" className="hover:text-white transition">
                  Front Desk Request
                </Link>
              </li>
            </ul>
          </div>

          {/* Security & Policies */}
          <div>
            <h4 className="text-white font-semibold text-xs uppercase tracking-wider mb-3">Security & Governance</h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>End-to-End Encryption</li>
              <li>Verified Email Constraint</li>
              <li>Role-Based Access Control</li>
              <li>Protected Health Information</li>
            </ul>
          </div>

          {/* Contact & Urgent Care */}
          <div>
            <h4 className="text-white font-semibold text-xs uppercase tracking-wider mb-3">Emergency & Desk</h4>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="font-semibold text-white">Emergency: 911 / 108</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-sky-400 shrink-0" />
                <span>support@cliniccarehospital.com</span>
              </div>
              <div className="flex items-start gap-2 text-slate-400">
                <MapPin className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                <span>Healthcare Complex, Medical District</span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
          <p>© {new Date().getFullYear()} ClinicCare Multispeciality Healthcare. All rights reserved.</p>
          <p className="text-[11px] text-slate-500">
            For life-threatening medical emergencies, please immediately contact your local emergency services.
          </p>
        </div>
      </div>
    </footer>
  )
}
