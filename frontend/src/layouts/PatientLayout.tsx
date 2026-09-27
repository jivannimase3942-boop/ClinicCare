import React from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from '@/components/layout/Navbar'
import { PatientSidebar } from '@/components/layout/PatientSidebar'
import { AIChatWidget } from '@/components/chat/AIChatWidget'

export const PatientLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex-1 flex max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 gap-6">
        <PatientSidebar />
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
      <AIChatWidget />
    </div>
  )
}
