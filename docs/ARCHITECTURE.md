# CarePulse Hospital AI Automation — System Architecture

## Overview
CarePulse is an enterprise-grade, full-stack Hospital AI Automation and Patient Care Orchestration platform engineered with FastAPI (Python 3.11), SQLAlchemy, PostgreSQL, Redis, React 18, TypeScript, Tailwind CSS, TanStack Query, and an autonomous AI Clinical Assistant service.

```
+-----------------------------------------------------------------------------------+
|                                Client Applications                                |
|  - React 18 / TypeScript Patient Portal                                           |
|  - Doctor / Physician Management Workspace                                        |
|  - Admin & Analytics Dashboard (Recharts)                                         |
|  - WhatsApp Business Webhook Client & Twilio Voice Gateways                       |
+-----------------------------------------------------------------------------------+
                                         | (HTTPS / REST / JSON)
                                         v
+-----------------------------------------------------------------------------------+
|                        CarePulse FastAPI Gateway & Security                       |
|  - JWT Bearer Authentication & Strict Role-Based Access Control (RBAC)            |
|  - IDOR Prevention via Authenticated Patient Context Injection                    |
|  - Global Exception Interceptor & Automated Error Log Recorder                    |
|  - CORS & Secure Request Throttling                                               |
+-----------------------------------------------------------------------------------+
                                         |
         +-------------------------------+-------------------------------+
         |                               |                               |
         v                               v                               v
+------------------+           +-------------------+           +--------------------+
|  Business Logic  |           | Medical AI Agent  |           | Async Automation   |
|  - AuthService   |           | - Clinical Triage |           | - n8n Workflows    |
|  - DoctorService |           | - Safe Guardrails |           | - WhatsApp Delivery|
|  - ApptService   |           | - 8 Tool Functions|           | - Voice Callback   |
|  - ReportService |           | - Gemini Pro Core |           | - Redis Queue      |
+------------------+           +-------------------+           +--------------------+
         |                               |                               |
         +-------------------------------+-------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           Relational Data Persistence                             |
|  - PostgreSQL 15 / SQLite In-Memory Engine                                        |
|  - 14 Domain Models: Users, Patients, Doctors, Departments, Appointments, Slots,   |
|    Reports, Feedback, AI Conversations, Messages, Voice Requests, Escalations     |
+-----------------------------------------------------------------------------------+
```

## Security & Access Control
- **Authentication**: JWT token with HMAC-SHA256 signature, 24h expiration.
- **Strict Role-Based Access Control (RBAC)**:
  - `PATIENT`: Access only their own appointments, medical lab reports, and AI chat sessions.
  - `DOCTOR`: View their own consultations, complete patient visits, and note diagnoses.
  - `ADMIN` & `FRONT_DESK`: Comprehensive access to hospital statistics, patient directory, slot configs, reports, escalations, and system error logs.
- **IDOR Protection**: All patient data routes derive `patient_id` exclusively from validated JWT claims.
