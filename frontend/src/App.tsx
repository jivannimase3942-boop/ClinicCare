import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/context/ToastContext'
import { AuthProvider } from '@/context/AuthContext'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'

// Layouts
import { PublicLayout } from '@/layouts/PublicLayout'
import { PatientLayout } from '@/layouts/PatientLayout'
import { AdminLayout } from '@/layouts/AdminLayout'
import { DoctorLayout } from '@/layouts/DoctorLayout'
import { FrontDeskLayout } from '@/layouts/FrontDeskLayout'

// Public & Auth Pages
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RoleSelectPage } from '@/pages/auth/RoleSelectPage'
import { PatientRegisterPage } from '@/pages/auth/PatientRegisterPage'
import { DoctorRegisterPage } from '@/pages/auth/DoctorRegisterPage'
import { FrontDeskRegisterPage } from '@/pages/auth/FrontDeskRegisterPage'

// Patient Pages
import { PatientDashboard } from '@/pages/patient/PatientDashboard'
import { DoctorsPage } from '@/pages/patient/DoctorsPage'
import { BookAppointmentPage } from '@/pages/patient/BookAppointmentPage'
import { AppointmentsPage } from '@/pages/patient/AppointmentsPage'
import { ReportsPage } from '@/pages/patient/ReportsPage'
import { FeedbackPage } from '@/pages/patient/FeedbackPage'
import { ProfilePage } from '@/pages/patient/ProfilePage'
import { AIChatPage } from '@/pages/patient/AIChatPage'
import { VoiceRequestPage } from '@/pages/patient/VoiceRequestPage'
import { AmbulancePage } from '@/pages/patient/AmbulancePage'
import { BloodSearchPage } from '@/pages/patient/BloodSearchPage'
import { FacilitiesPage } from '@/pages/patient/FacilitiesPage'
import { VisitHistoryPage } from '@/pages/patient/VisitHistoryPage'
import { RemindersPage } from '@/pages/patient/RemindersPage'

// Admin Pages
import { AdminDashboard } from '@/pages/admin/AdminDashboard'
import { AdminPatients } from '@/pages/admin/AdminPatients'
import { AdminDoctors } from '@/pages/admin/AdminDoctors'
import { AdminDepartments } from '@/pages/admin/AdminDepartments'
import { AdminAppointments } from '@/pages/admin/AdminAppointments'
import { AdminReports } from '@/pages/admin/AdminReports'
import { AdminFeedback } from '@/pages/admin/AdminFeedback'
import { AdminEscalations } from '@/pages/admin/AdminEscalations'
import { AdminVoiceCalls } from '@/pages/admin/AdminVoiceCalls'
import { AdminConversations } from '@/pages/admin/AdminConversations'
import { AdminErrors } from '@/pages/admin/AdminErrors'
import { AdminAmbulances } from '@/pages/admin/AdminAmbulances'
import { AdminBloodBank } from '@/pages/admin/AdminBloodBank'
import { AdminFacilities } from '@/pages/admin/AdminFacilities'
import { AdminEmergency } from '@/pages/admin/AdminEmergency'
import { AdminReminders } from '@/pages/admin/AdminReminders'

// Doctor Pages
import { DoctorDashboard } from '@/pages/doctor/DoctorDashboard'
import { DoctorAppointments } from '@/pages/doctor/DoctorAppointments'

// Front Desk Pages
import { FrontDeskDashboard } from '@/pages/frontdesk/FrontDeskDashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
})

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route element={<PublicLayout />}>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RoleSelectPage />} />
                <Route path="/register/patient" element={<PatientRegisterPage />} />
                <Route path="/register/doctor" element={<DoctorRegisterPage />} />
                <Route path="/register/frontdesk" element={<FrontDeskRegisterPage />} />
              </Route>

              {/* Patient Routes */}
              <Route
                path="/patient"
                element={
                  <ProtectedRoute allowedRoles={['PATIENT', 'ADMIN']}>
                    <PatientLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/patient/dashboard" replace />} />
                <Route path="dashboard" element={<PatientDashboard />} />
                <Route path="doctors" element={<DoctorsPage />} />
                <Route path="appointments" element={<AppointmentsPage />} />
                <Route path="appointments/book" element={<BookAppointmentPage />} />
                <Route path="ambulance" element={<AmbulancePage />} />
                <Route path="blood" element={<BloodSearchPage />} />
                <Route path="facilities" element={<FacilitiesPage />} />
                <Route path="visits" element={<VisitHistoryPage />} />
                <Route path="reminders" element={<RemindersPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="feedback" element={<FeedbackPage />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="chat" element={<AIChatPage />} />
                <Route path="voice-request" element={<VoiceRequestPage />} />
              </Route>

              {/* Doctor Routes */}
              <Route
                path="/doctor"
                element={
                  <ProtectedRoute allowedRoles={['DOCTOR', 'ADMIN']}>
                    <DoctorLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/doctor/dashboard" replace />} />
                <Route path="dashboard" element={<DoctorDashboard />} />
                <Route path="appointments" element={<DoctorAppointments />} />
              </Route>

              {/* Front Desk Routes */}
              <Route
                path="/frontdesk"
                element={
                  <ProtectedRoute allowedRoles={['FRONT_DESK', 'ADMIN']}>
                    <FrontDeskLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/frontdesk/dashboard" replace />} />
                <Route path="dashboard" element={<FrontDeskDashboard />} />
                <Route path="patients" element={<AdminPatients />} />
                <Route path="appointments" element={<AdminAppointments />} />
                <Route path="doctors" element={<AdminDoctors />} />
                <Route path="emergency" element={<AdminEmergency />} />
                <Route path="ambulances" element={<AdminAmbulances />} />
                <Route path="escalations" element={<AdminEscalations />} />
              </Route>

              {/* Admin Routes - Strictly ADMIN role */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="emergency" element={<AdminEmergency />} />
                <Route path="ambulances" element={<AdminAmbulances />} />
                <Route path="blood-bank" element={<AdminBloodBank />} />
                <Route path="facilities" element={<AdminFacilities />} />
                <Route path="patients" element={<AdminPatients />} />
                <Route path="doctors" element={<AdminDoctors />} />
                <Route path="departments" element={<AdminDepartments />} />
                <Route path="appointments" element={<AdminAppointments />} />
                <Route path="reminders" element={<AdminReminders />} />
                <Route path="reports" element={<AdminReports />} />
                <Route path="feedback" element={<AdminFeedback />} />
                <Route path="escalations" element={<AdminEscalations />} />
                <Route path="voice-calls" element={<AdminVoiceCalls />} />
                <Route path="conversations" element={<AdminConversations />} />
                <Route path="errors" element={<AdminErrors />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  )
}

export default App
