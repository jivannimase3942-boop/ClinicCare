import React from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from '@/components/layout/Navbar'
import { AdminSidebar } from '@/components/layout/AdminSidebar'

export const AdminLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar />
      <div className="flex-1 flex">
        <AdminSidebar />
        <main className="flex-1 p-6 md:p-8 bg-slate-900 overflow-x-hidden min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
