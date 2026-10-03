export type UserRole =
  | 'PATIENT'
  | 'DOCTOR'
  | 'ADMIN'
  | 'FRONT_DESK'
  | 'PENDING_DOCTOR'
  | 'PENDING_FRONT_DESK'
  | 'SUPER_ADMIN'
  | 'BRANCH_ADMIN'
  | 'NURSE'
  | 'PHARMACIST'
  | 'LAB_TECHNICIAN'
  | 'RADIOLOGIST'
  | 'ACCOUNTANT'
  | 'AMBULANCE_COORDINATOR'

export interface PatientProfile {
  id: string
  date_of_birth?: string | null
  gender?: string | null
  blood_group?: string | null
  address?: string | null
  emergency_contact?: string | null
}

export interface DoctorProfile {
  id: string
  department_id: string
  department_name?: string | null
  specialization: string
  qualification: string
  experience_years: number
  consultation_fee: number
  location: string
  available_days: string
  available_hours_start: string
  available_hours_end: string
  profile_image?: string | null
}

export interface User {
  id: string
  email: string
  full_name: string
  phone?: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  patient_profile?: PatientProfile | null
  doctor_profile?: DoctorProfile | null
  clinic_id?: string | null
  clinic_name?: string | null
  permissions?: string[] | null
}

export interface Clinic {
  id: string
  name: string
  slug: string
  phone?: string | null
  email?: string | null
  address?: string | null
  city?: string | null
  state?: string | null
  pincode?: string | null
  country?: string | null
  operating_hours: string
  consultation_fee_default: number
  is_active: boolean
  settings_json?: string | null
  created_at: string
  updated_at?: string
}

export interface AuditLog {
  id: string
  clinic_id?: string | null
  user_id?: string | null
  user_email?: string | null
  user_role?: string | null
  action: string
  entity_type?: string | null
  entity_id?: string | null
  details?: string | null
  ip_address?: string | null
  user_agent?: string | null
  created_at: string
}

export interface Department {
  id: string
  name: string
  description?: string | null
  icon: string
  is_active: boolean
  created_at: string
}

export interface Doctor {
  id: string
  user_id: string
  full_name: string
  email: string
  phone?: string | null
  department_id: string
  department_name?: string | null
  specialization: string
  qualification: string
  experience_years: number
  consultation_fee: number
  location: string
  available_days: string
  available_hours_start: string
  available_hours_end: string
  slot_duration_minutes: number
  profile_image?: string | null
  is_active: boolean
}

export interface DoctorSlot {
  id: string
  doctor_id: string
  slot_date: string
  start_time: string
  end_time: string
  is_booked: boolean
}

export type AppointmentStatus =
  | 'pending'
  | 'confirmed'
  | 'checked_in'
  | 'waiting'
  | 'in_consultation'
  | 'completed'
  | 'cancelled'
  | 'rescheduled'
  | 'no_show'

export type AppointmentType =
  | 'NEW_CONSULTATION'
  | 'FOLLOW_UP'
  | 'PROCEDURE'
  | 'TELECONSULTATION'
  | 'EMERGENCY'
  | 'HOME_VISIT'

export type QueueStatus =
  | 'NOT_QUEUED'
  | 'WAITING'
  | 'CALLED'
  | 'IN_CONSULTATION'
  | 'COMPLETED'
  | 'SKIPPED'
  | 'CANCELLED'

export interface Appointment {
  id: string
  clinic_id?: string | null
  clinic_name?: string | null
  patient_id: string
  patient_name?: string | null
  patient_email?: string | null
  patient_phone?: string | null
  doctor_id: string
  doctor_name?: string | null
  department_name?: string | null
  appointment_date: string
  appointment_time: string
  status: AppointmentStatus
  appointment_type?: AppointmentType | string
  token_number?: string | null
  queue_status?: QueueStatus | string
  checked_in_at?: string | null
  consultation_started_at?: string | null
  consultation_ended_at?: string | null
  is_walk_in?: boolean
  parent_appointment_id?: string | null
  reason?: string | null
  notes?: string | null
  cancellation_reason?: string | null
  cancelled_reason?: string | null
  created_at: string
  updated_at: string
}

export interface InvoiceItem {
  id: string
  item_type: 'CONSULTATION' | 'PROCEDURE' | 'LAB_TEST' | 'MEDICINE' | 'SERVICE' | string
  description: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface PaymentRecord {
  id: string
  invoice_id: string
  amount: number
  payment_method: 'CASH' | 'UPI' | 'CARD' | 'ONLINE_GATEWAY' | 'BANK_TRANSFER' | string
  transaction_reference?: string | null
  notes?: string | null
  created_at: string
}

export interface RefundRecord {
  id: string
  invoice_id: string
  amount: number
  reason: string
  status: string
  created_at: string
}

export interface Invoice {
  id: string
  invoice_number: string
  clinic_id: string
  clinic_name?: string | null
  clinic_phone?: string | null
  clinic_address?: string | null
  patient_id: string
  patient_name?: string | null
  patient_phone?: string | null
  appointment_id?: string | null
  doctor_id?: string | null
  doctor_name?: string | null
  subtotal: number
  discount_amount: number
  tax_rate_percent: number
  tax_amount: number
  total_amount: number
  amount_paid: number
  balance_due: number
  status: 'PENDING' | 'PARTIALLY_PAID' | 'PAID' | 'REFUNDED' | 'CANCELLED'
  payment_method?: string | null
  notes?: string | null
  items: InvoiceItem[]
  payments: PaymentRecord[]
  refunds: RefundRecord[]
  created_at: string
  updated_at: string
}

export interface RevenueSummary {
  today_revenue: number
  weekly_revenue: number
  monthly_revenue: number
  consultation_revenue: number
  procedure_revenue: number
  payment_methods: Record<string, number>
  pending_dues: number
  total_refunds: number
  invoice_count: number
}

export interface WaitlistEntry {
  id: string
  clinic_id?: string | null
  patient_id: string
  patient_name?: string | null
  patient_phone?: string | null
  doctor_id: string
  doctor_name?: string | null
  desired_date: string
  preferred_time_range?: string | null
  status: string
  notes?: string | null
  created_at: string
}

export type ReportStatus = 'pending' | 'processing' | 'ready' | 'delivered' | 'failed'

export interface MedicalReport {
  id: string
  patient_id: string
  patient_name?: string | null
  doctor_id?: string | null
  doctor_name?: string | null
  title: string
  report_type: string
  status: ReportStatus
  summary?: string | null
  file_url?: string | null
  report_date: string
  delivered_at?: string | null
  created_at: string
}

export interface Feedback {
  id: string
  patient_id: string
  patient_name?: string | null
  appointment_id?: string | null
  rating: number
  comment?: string | null
  status: string
  created_at: string
}

export type EscalationReason =
  | 'medical_question'
  | 'emergency'
  | 'billing'
  | 'complaint'
  | 'technical_issue'
  | 'patient_requested_call'
  | 'ai_uncertain'
  | 'other'

export type EscalationStatus = 'open' | 'assigned' | 'in_progress' | 'resolved' | 'closed'
export type EscalationPriority = 'low' | 'medium' | 'high' | 'urgent'

export interface Escalation {
  id: string
  patient_id: string
  patient_name?: string | null
  patient_phone?: string | null
  reason: EscalationReason
  message: string
  priority: EscalationPriority
  status: EscalationStatus
  assigned_to?: string | null
  assigned_to_name?: string | null
  admin_notes?: string | null
  resolved_at?: string | null
  created_at: string
}

export type VoiceCallStatus = 'requested' | 'queued' | 'calling' | 'completed' | 'failed' | 'cancelled'

export interface VoiceCallRequest {
  id: string
  patient_id: string
  patient_name?: string | null
  phone?: string | null
  reason: string
  status: VoiceCallStatus
  requested_at: string
  completed_at?: string | null
  notes?: string | null
  created_at: string
}

export interface AIMessage {
  id: string
  role?: 'user' | 'assistant' | 'system'
  sender?: string
  content: string
  intent?: string | null
  language?: string | null
  created_at: string
}

export interface AIConversation {
  id: string
  patient_id?: string | null
  patient_name?: string | null
  channel: string
  created_at: string
  updated_at: string
  messages: AIMessage[]
}

export interface AIChatResponse {
  conversation_id: string
  response: string
  intent?: string | null
  tool_calls_executed?: string[]
  escalation_triggered: boolean
  is_emergency: boolean
}

export interface MetricSummary {
  total_patients: number
  total_doctors: number
  today_appointments: number
  upcoming_appointments: number
  pending_appointments: number
  completed_appointments: number
  cancelled_appointments: number
  pending_reports: number
  open_escalations: number
  active_ambulances: number
  emergency_requests: number
  available_blood_units: number
  feedback_count: number
  ai_conversations_count: number
  average_rating: number
}

export interface ChartDataPoint {
  label: string
  value: number
}

export interface AdminDashboardStats {
  metrics: MetricSummary
  appointments_by_day: ChartDataPoint[]
  appointment_status_distribution: ChartDataPoint[]
  feedback_ratings_distribution: ChartDataPoint[]
  report_status_distribution: ChartDataPoint[]
  ai_conversations_trend: ChartDataPoint[]
}

export interface Ambulance {
  id: string
  vehicle_number: string
  model: string
  ambulance_type: string
  status: 'available' | 'busy' | 'offline' | 'maintenance'
  base_station: string
  current_location: string
  driver_name?: string | null
  driver_phone?: string | null
  paramedic_name?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AmbulanceRequest {
  id: string
  patient_id?: string | null
  patient_name?: string | null
  ambulance_id?: string | null
  ambulance_vehicle_number?: string | null
  ambulance_model?: string | null
  driver_name?: string | null
  driver_phone?: string | null
  requester_name: string
  requester_phone: string
  pickup_address: string
  destination_facility: string
  emergency_priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'requested' | 'assigned' | 'en_route' | 'arrived' | 'completed' | 'cancelled'
  notes?: string | null
  is_simulated: boolean
  created_at: string
  updated_at: string
}

export interface BloodInventoryItem {
  id: string
  blood_bank_id: string
  blood_group: string
  units_available: number
  status: string
  last_updated: string
}

export interface BloodBank {
  id: string
  name: string
  city: string
  address: string
  phone: string
  email?: string | null
  operating_hours: string
  is_verified: boolean
  inventory: BloodInventoryItem[]
  created_at: string
  updated_at: string
}

export interface BloodGroupSearchResult {
  blood_bank_id: string
  blood_bank_name: string
  city: string
  address: string
  phone: string
  blood_group: string
  units_available: number
  status: string
  last_updated: string
  operating_hours: string
}

export type BloodRequestStatus =
  | 'submitted'
  | 'searching'
  | 'match_found'
  | 'fulfilled'
  | 'cancelled'

export interface BloodRequest {
  id: string
  patient_id?: string | null
  patient_name: string
  blood_group: string
  units_required: number
  hospital_clinic_name: string
  location: string
  contact_phone: string
  urgency: 'normal' | 'urgent' | 'critical'
  additional_info?: string | null
  status: BloodRequestStatus
  matched_blood_bank_id?: string | null
  matched_bank_name?: string | null
  admin_notes?: string | null
  is_simulated: boolean
  created_at: string
  updated_at: string
}

export interface Facility {
  id: string
  name: string
  facility_type: string
  services: string
  address: string
  city: string
  phone: string
  emergency_hotline: string
  operating_hours: string
  is_emergency_ready: boolean
  rating: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface VisitHistory {
  id: string
  patient_id: string
  patient_name?: string | null
  doctor_id?: string | null
  doctor_name?: string | null
  department_id?: string | null
  department_name?: string | null
  appointment_id?: string | null
  visit_date: string
  visit_type: string
  visit_status: string
  vitals_summary?: string | null
  administrative_notes?: string | null
  follow_up_instructions?: string | null
  created_at: string
}

export interface FollowUpReminder {
  id: string
  patient_id: string
  patient_name?: string | null
  patient_phone?: string | null
  appointment_id?: string | null
  doctor_id?: string | null
  doctor_name?: string | null
  reminder_type: string
  scheduled_for: string
  title: string
  message: string
  channel: string
  status: 'scheduled' | 'pending' | 'sent_demo' | 'failed' | 'cancelled'
  sent_at?: string | null
  created_at: string
}

export interface EmergencyRequest {
  id: string
  patient_id?: string | null
  patient_name?: string | null
  caller_name: string
  caller_phone: string
  location: string
  emergency_type: string
  priority: string
  status: string
  ambulance_id?: string | null
  ambulance_vehicle_number?: string | null
  assigned_staff_id?: string | null
  assigned_staff_name?: string | null
  resolution_notes?: string | null
  created_at: string
  updated_at: string
}

export interface EmergencyStats {
  total_emergencies: number
  critical_active: number
  dispatched_ambulances: number
  resolved_today: number
  average_response_minutes: number
}


export interface ErrorLog {
  id: string
  service_name: string
  error_level: string
  message: string
  stack_trace?: string | null
  endpoint?: string | null
  context_json?: string | null
  created_at: string
}

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data: T
  error_code?: string
}
