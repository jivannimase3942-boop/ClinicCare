export type UserRole =
  | 'PATIENT'
  | 'DOCTOR'
  | 'ADMIN'
  | 'FRONT_DESK'
  | 'PENDING_DOCTOR'
  | 'PENDING_FRONT_DESK'
  | 'SUPER_ADMIN'
  | 'ORGANIZATION_ADMIN'
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
  organization_id?: string | null
  branch_id?: string | null
  permissions?: string[] | null
}

export interface Branch {
  id: string
  organization_id: string
  clinic_id?: string | null
  name: string
  code: string
  address?: string | null
  city: string
  state: string
  pincode?: string | null
  phone?: string | null
  email?: string | null
  operating_hours: string
  branch_admin_user_id?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  stats?: {
    total_doctors: number
    total_appointments: number
    total_patients: number
    total_invoices: number
    total_revenue_inr: number
  }
}

export interface Organization {
  id: string
  name: string
  code: string
  description?: string | null
  email?: string | null
  phone?: string | null
  website?: string | null
  headquarters_address?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  branches?: Branch[]
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
  total_revenue: number
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

export interface VitalSign {
  id: string
  clinic_id: string
  patient_id: string
  appointment_id?: string | null
  consultation_id?: string | null
  temperature_celsius?: number | null
  pulse_bpm?: number | null
  bp_systolic?: number | null
  bp_diastolic?: number | null
  respiratory_rate?: number | null
  spo2_percent?: number | null
  weight_kg?: number | null
  height_cm?: number | null
  bmi?: number | null
  notes?: string | null
  recorded_at: string
  created_at: string
}

export interface ConsultationRecord {
  id: string
  clinic_id: string
  patient_id: string
  patient_name?: string | null
  doctor_id: string
  doctor_name?: string | null
  doctor_specialization?: string | null
  appointment_id?: string | null
  status: 'DRAFT' | 'FINALIZED' | 'AMENDED'
  version: number
  chief_complaint: string
  history_of_present_illness?: string | null
  medical_history?: string | null
  allergies?: string | null
  lifestyle_notes?: string | null
  examination_notes?: string | null
  diagnosis: string
  treatment_plan?: string | null
  investigations_ordered?: string | null
  follow_up_date?: string | null
  referral?: string | null
  clinical_notes?: string | null
  is_finalized: boolean
  finalized_at?: string | null
  created_at: string
  updated_at: string
  vitals?: VitalSign[]
}

export interface ClinicalDocument {
  id: string
  clinic_id: string
  patient_id: string
  consultation_id?: string | null
  document_type: string
  title: string
  file_url: string
  file_type: string
  file_size_bytes: number
  description?: string | null
  created_at: string
}

export interface TimelineItem {
  event_type: 'CONSULTATION' | 'VITAL_SIGN' | 'DOCUMENT' | 'APPOINTMENT' | 'REPORT'
  event_id: string
  timestamp: string
  title: string
  subtitle?: string | null
  status?: string | null
  doctor_name?: string | null
  department_name?: string | null
  details: Record<string, any>
}

export interface PatientTimeline {
  patient_id: string
  patient_name: string
  total_events: number
  events: TimelineItem[]
}

export interface Medicine {
  id: string
  clinic_id?: string | null
  brand_name: string
  generic_name: string
  strength: string
  dosage_form: string
  manufacturer?: string | null
  category: string
  hsn_code?: string | null
  gst_rate_percent: number
  unit_price: number
  is_active: boolean
  created_at: string
}

export interface PrescriptionItem {
  id?: string
  prescription_id?: string
  medicine_id?: string | null
  medicine_name: string
  generic_name?: string | null
  dosage_form: string
  strength?: string | null
  dosage: string
  frequency: string
  duration: string
  route: string
  instructions: string
  quantity: number
}

export interface Prescription {
  id: string
  prescription_number: string
  clinic_id: string
  clinic_name?: string | null
  clinic_address?: string | null
  clinic_phone?: string | null
  patient_id: string
  patient_name?: string | null
  patient_phone?: string | null
  patient_gender?: string | null
  doctor_id: string
  doctor_name?: string | null
  doctor_specialization?: string | null
  doctor_qualification?: string | null
  appointment_id?: string | null
  consultation_id?: string | null
  status: 'DRAFT' | 'FINALIZED' | 'ISSUED' | 'CANCELLED'
  diagnosis_summary: string
  general_advice?: string | null
  diet_lifestyle_notes?: string | null
  follow_up_date?: string | null
  is_finalized: boolean
  finalized_at?: string | null
  items: PrescriptionItem[]
  created_at: string
  updated_at: string
}

export interface LabTest {
  id: string
  clinic_id?: string | null
  name: string
  code: string
  category: string
  sample_type: string
  turnaround_hours: number
  price: number
  normal_range?: string | null
  unit?: string | null
  is_active: boolean
  created_at: string
}

export interface LabSample {
  id: string
  lab_order_id: string
  barcode_number: string
  sample_type: string
  status: string
  rejection_reason?: string | null
  collected_at?: string | null
  collected_by_name?: string | null
  created_at: string
}

export interface LabResult {
  id: string
  lab_order_id: string
  lab_test_id: string
  test_name?: string | null
  parameter_name: string
  result_value: string
  unit?: string | null
  reference_range?: string | null
  is_abnormal: boolean
  technician_notes?: string | null
  tested_by_name?: string | null
  created_at: string
}

export interface LabReport {
  id: string
  report_number: string
  lab_order_id: string
  clinic_id: string
  clinic_name?: string | null
  clinic_address?: string | null
  patient_id: string
  patient_name?: string | null
  doctor_name?: string | null
  is_validated: boolean
  validated_at?: string | null
  validated_by_name?: string | null
  is_released: boolean
  released_at?: string | null
  summary_notes?: string | null
  results: LabResult[]
  created_at: string
}

export interface LabOrder {
  id: string
  order_number: string
  clinic_id: string
  patient_id: string
  patient_name?: string | null
  doctor_id: string
  doctor_name?: string | null
  appointment_id?: string | null
  priority: 'ROUTINE' | 'URGENT' | 'STAT'
  status: 'ORDERED' | 'SAMPLE_PENDING' | 'SAMPLE_COLLECTED' | 'PROCESSING' | 'RESULT_READY' | 'VALIDATED' | 'CANCELLED'
  clinical_notes?: string | null
  tests: LabTest[]
  samples: LabSample[]
  results: LabResult[]
  report?: LabReport | null
  created_at: string
  updated_at: string
}

export interface Supplier {
  id: string
  clinic_id: string
  name: string
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  gstin?: string | null
  dl_number?: string | null
  address?: string | null
  is_active: boolean
  created_at: string
}

export interface StockBatch {
  id: string
  clinic_id: string
  medicine_id: string
  medicine_name?: string | null
  generic_name?: string | null
  dosage_form?: string | null
  supplier_id?: string | null
  supplier_name?: string | null
  batch_number: string
  expiry_date: string
  purchase_price: number
  mrp: number
  sale_price: number
  initial_quantity: number
  current_quantity: number
  reorder_threshold: number
  is_active: boolean
  is_expired: boolean
  is_near_expiry: boolean
  is_low_stock: boolean
  created_at: string
  updated_at: string
}

export interface StockTransaction {
  id: string
  clinic_id: string
  batch_id: string
  batch_number?: string | null
  medicine_id: string
  medicine_name?: string | null
  transaction_type: string
  quantity: number
  balance_after: number
  unit_price: number
  invoice_id?: string | null
  prescription_id?: string | null
  reason?: string | null
  actor_name?: string | null
  created_at: string
}

export interface StockAlert {
  batch_id: string
  batch_number: string
  medicine_id: string
  medicine_name: string
  expiry_date: string
  current_quantity: number
  reorder_threshold: number
  alert_type: 'EXPIRED' | 'NEAR_EXPIRY' | 'LOW_STOCK'
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  message: string
}
