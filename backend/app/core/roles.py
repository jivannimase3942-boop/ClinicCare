from typing import List, Dict, Set

class Role:
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    FRONT_DESK = "FRONT_DESK"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    BRANCH_ADMIN = "BRANCH_ADMIN"
    NURSE = "NURSE"
    PHARMACIST = "PHARMACIST"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    RADIOLOGIST = "RADIOLOGIST"
    ACCOUNTANT = "ACCOUNTANT"
    AMBULANCE_COORDINATOR = "AMBULANCE_COORDINATOR"
    PENDING_DOCTOR = "PENDING_DOCTOR"
    PENDING_FRONT_DESK = "PENDING_FRONT_DESK"


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    Role.SUPER_ADMIN: {"*"},
    Role.ORGANIZATION_ADMIN: {
        "view_organization",
        "manage_organization",
        "manage_branches",
        "view_branches",
        "view_clinic",
        "manage_clinic",
        "view_audit_logs",
        "manage_staff",
        "manage_doctors",
        "view_all_appointments",
        "manage_appointments",
        "view_reports",
        "view_analytics",
        "view_billing",
        "manage_billing",
    },
    Role.ADMIN: {
        "view_clinic",
        "manage_clinic",
        "view_audit_logs",
        "manage_staff",
        "manage_doctors",
        "view_all_appointments",
        "manage_appointments",
        "view_reports",
        "manage_facilities",
        "view_analytics",
        "view_errors",
    },
    Role.BRANCH_ADMIN: {
        "view_clinic",
        "manage_clinic",
        "view_audit_logs",
        "manage_staff",
        "manage_doctors",
        "view_all_appointments",
        "manage_appointments",
        "view_reports",
        "view_analytics",
    },
    Role.DOCTOR: {
        "view_assigned_appointments",
        "update_appointment_status",
        "view_patient_records",
        "create_clinical_notes",
        "create_reports",
        "view_reports",
        "view_doctor_availability",
    },
    Role.FRONT_DESK: {
        "view_appointments",
        "book_appointments",
        "reschedule_appointments",
        "cancel_appointments",
        "checkin_patient",
        "search_patients",
        "register_patient",
        "view_doctor_availability",
    },
    Role.PATIENT: {
        "view_own_profile",
        "edit_own_profile",
        "book_appointments",
        "view_own_appointments",
        "cancel_own_appointments",
        "view_own_reports",
        "submit_feedback",
        "ai_assistant",
    },
    Role.NURSE: {
        "view_appointments",
        "view_patient_records",
        "record_vitals",
        "view_queue",
    },
    Role.PHARMACIST: {
        "view_prescriptions",
        "dispense_medicine",
        "view_inventory",
    },
    Role.LAB_TECHNICIAN: {
        "view_lab_orders",
        "update_lab_status",
        "upload_reports",
    },
    Role.RADIOLOGIST: {
        "view_imaging_requests",
        "upload_imaging_reports",
    },
    Role.ACCOUNTANT: {
        "view_invoices",
        "manage_billing",
        "view_financial_reports",
    },
    Role.AMBULANCE_COORDINATOR: {
        "manage_ambulances",
        "dispatch_emergency",
    },
    Role.PENDING_DOCTOR: set(),
    Role.PENDING_FRONT_DESK: set(),
}


def get_permissions_for_role(role: str) -> List[str]:
    role_upper = (role or "").upper()
    perms = ROLE_PERMISSIONS.get(role_upper, set())
    return sorted(list(perms))


def has_permission(role: str, permission: str) -> bool:
    role_upper = (role or "").upper()
    perms = ROLE_PERMISSIONS.get(role_upper, set())
    return "*" in perms or permission in perms
