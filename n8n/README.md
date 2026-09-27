# Hospital AI Automation — n8n Master Workflow Architecture

This directory contains the n8n automated workflow specification for:
**"Hospital AI Automation — Appointments + WhatsApp Support + Voice Calls + Reports + Feedback"**

## Included Workflows

### 1. Master Workflow (`workflows/Hospital AI Automation — Appointments + WhatsApp Support + Voice Calls + Reports + Feedback.json` & `workflows/hospital-ai-automation-main.json`)
The complete end-to-end automation engine matching the JSON master specification:

1. **WhatsApp Inbound & Verification Webhook**:
   - `GET /whatsapp-webhook`: Meta verification handshake (`hub.mode`, `hub.verify_token`, `hub.challenge`).
   - `POST /whatsapp-webhook`: Processes incoming WhatsApp messages with automatic classification.
2. **Pending Feedback Rating Interception**:
   - Detects if patient has completed appointments awaiting feedback and is replying with a 1-5 rating.
   - Records feedback directly into database (`feedback` table).
   - Returns gratitude acknowledgment via WhatsApp.
3. **Patient WhatsApp AI Agent with Tools**:
   - Tool 1: `Get Hospital and Doctor Info`
   - Tool 2: `Check Doctor's Booked Slots`
   - Tool 3: `Book Appointment` (requires department & doctor confirmation)
   - Tool 4: `Reschedule Appointment`
   - Tool 5: `Cancel Appointment`
   - Tool 6: `Check My Report Status` (Diagnostic reports & prescriptions)
   - Tool 7: `Request AI Voice Call For This Patient`
   - Tool 8: `Escalate To Front Desk (Human Handoff)` (complaints, billing, emergencies, medical questions)
4. **Scheduled Workflows**:
   - `Hourly Appointment Reminders`: Scans upcoming 24h appointments and dispatches reminders.
   - `Scheduled Feedback Scanner`: Scans completed consultations and triggers 1-5 rating requests.
   - `Report Ready Notifications`: Dispatches alerts when diagnostic reports transition to ready.
5. **Global Error Alerting Pipeline**:
   - Captures workflow failures.
   - Builds alert message payload.
   - Dispatches error alert email via SMTP to administrator.
   - Persists error log in Supabase / SQLite `error_logs` table.

### 2. Appointment Reminders Subflow (`workflows/hospital-appointment-reminders.json`)
- Dedicated hourly cron schedule for targeted appointment reminders.

## How to Import & Run in n8n

1. Start n8n using Docker:
   ```bash
   docker-compose up -d n8n
   ```
2. Navigate to `http://localhost:5678` in your browser.
3. Log in using `admin` / `AdminHospital2026!`.
4. Click **Workflows** -> **Import from File...**
5. Select `n8n/workflows/hospital-ai-automation-main.json`.
6. Configure environment variables in `.env` and activate workflow.

