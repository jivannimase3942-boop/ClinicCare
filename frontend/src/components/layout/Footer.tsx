import React from 'react'
import { Activity, Heart, Shield, Phone, Mail, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-teal-400 flex items-center justify-center text-white font-bold">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-xl font-black text-white tracking-tight">ClinicCare AI</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Next-generation autonomous healthcare intelligence platform connecting patients with specialized clinicians with AI assistance.
            </p>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Shield className="w-4 h-4 text-emerald-400" /> HIPAA Compliant Architecture
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Patient Portal</h4>
            <ul className="space-y-2.5 text-xs">
              <li>
                <Link to="/patient/appointments/book" className="hover:text-white transition">
                  Book Appointment
                </Link>
              </li>
              <li>
                <Link to="/patient/doctors" className="hover:text-white transition">
                  Find Doctors & Specialists
                </Link>
              </li>
              <li>
                <Link to="/patient/reports" className="hover:text-white transition">
                  Medical Reports
                </Link>
              </li>
              <li>
                <Link to="/patient/chat" className="hover:text-white transition">
                  AI Health Assistant
                </Link>
              </li>
            </ul>
          </div>

          {/* Departments */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Top Departments</h4>
            <ul className="space-y-2.5 text-xs">
              <li>Cardiology & Heart Care</li>
              <li>Neurology & Spine Surgery</li>
              <li>Orthopedics & Joint Clinic</li>
              <li>Pediatrics & Neonatal</li>
              <li>Dermatology & Skin Care</li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Emergency & Contact</h4>
            <div className="space-y-3 text-xs">
              <div className="flex items-start gap-2.5">
                <MapPin className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <span>ClinicCare Medical Complex, Health Avenue, Metro Hub</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Phone className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="font-semibold text-white">+1 (800) 555-CARE / 108</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Mail className="w-4 h-4 text-teal-400 shrink-0" />
                <span>support@cliniccare-hospital.com</span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-12 pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} ClinicCare. All rights reserved.</p>
          <div className="flex items-center gap-1 text-slate-500">
            <span>Engineered with medical safety guardrails</span>
            <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500 inline mx-1" />
          </div>
        </div>
      </div>
    </footer>
  )
}
