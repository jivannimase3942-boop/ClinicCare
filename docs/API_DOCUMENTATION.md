# ClinicCare API Specification & Endpoints

Base URL: `http://localhost:8000/api`

## Authentication (`/auth`)
- `POST /auth/register`: Register new user (Patient by default).
- `POST /auth/login`: Authenticate and obtain JWT bearer token.
- `GET /auth/me`: Get current authenticated user details and profile.
- `PATCH /auth/change-password`: Update password.

## Departments & Doctors (`/departments`, `/doctors`)
- `GET /departments`: List all active clinical departments.
- `GET /doctors`: List doctors with optional `department_id` and `search` query parameters.
- `GET /doctors/{id}`: Doctor profile details.
- `GET /doctors/{id}/slots?date=YYYY-MM-DD`: Available consultation time slots for a specific date.

## Appointments (`/appointments`)
- `POST /appointments`: Book an appointment (`doctor_id`, `appointment_date`, `appointment_time`, `reason`).
- `GET /appointments/my`: Get current patient's appointments.
- `GET /appointments/{id}`: Appointment details.
- `PATCH /appointments/{id}/reschedule`: Reschedule date and time slot.
- `PATCH /appointments/{id}/cancel`: Cancel appointment with optional reason.

## Medical Reports (`/reports`)
- `GET /reports/my`: Get current patient's lab and diagnostic reports.

## Feedback & Reviews (`/feedback`)
- `POST /feedback`: Submit patient review and 1-5 star rating.
- `GET /feedback/my`: Get reviews submitted by the patient.

## AI Assistant (`/ai`)
- `POST /ai/chat`: Send prompt to Medical AI with tool calling and clinical safety guardrails.
- `GET /ai/conversations`: List patient's past AI conversation sessions.
- `GET /ai/conversations/{id}`: Get full message history for a conversation.

## Voice Callbacks (`/voice`)
- `POST /voice/request`: Submit telephone callback request.
- `GET /voice/my`: Get patient callback requests.

## Escalations (`/escalations`)
- `POST /escalations`: Create escalation ticket to front desk.
- `GET /escalations/my`: Get patient's open escalations.

## Admin Management (`/admin`) [Requires `ADMIN` or `FRONT_DESK` role]
- `GET /admin/stats`: Comprehensive dashboard KPI metrics & distribution charts.
- `GET /admin/patients`: Full patient directory.
- `GET /admin/doctors`: Doctor roster and fee tables.
- `POST /admin/departments`: Create new hospital department.
- `GET /admin/appointments`: View all hospital appointments.
- `PATCH /admin/appointments/{id}/status`: Update appointment status (`confirmed`, `completed`, `cancelled`).
- `GET /admin/reports`: All diagnostic reports.
- `POST /admin/reports`: Generate new patient lab report.
- `PATCH /admin/reports/{id}/status`: Update report status.
- `GET /admin/feedback`: All patient satisfaction ratings.
- `GET /admin/escalations`: Open front desk tickets.
- `PATCH /admin/escalations/{id}`: Resolve or update escalation.
- `GET /admin/voice-calls`: Queue of telephone callback requests.
- `PATCH /admin/voice-calls/{id}`: Update callback status.
- `GET /admin/conversations`: AI chat logs for audits.
- `GET /admin/errors`: Backend and workflow exception logs.
