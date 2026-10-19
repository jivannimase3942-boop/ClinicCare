# ClinicCare

FIT-FEST 2026 Hackathon project.

ClinicCare is an intelligent administrative and healthcare coordination platform engineered to streamline patient appointments, emergency triage, ambulance dispatches, blood inventory search, and facility navigation with AI-assisted guidance.

## Problem Statement

Modern outpatient and emergency healthcare systems face fragmented coordination across administrative departments, specialist scheduling, emergency dispatches, blood availability, and patient inquiries. Patients struggle with long waiting lines, unclear scheduling, delayed emergency triage, and fragmented health record access, while administrative staff lack a unified dashboard for multi-department operations.

## Solution

ClinicCare bridges this gap by unifying critical healthcare administrative workflows into a single full-stack orchestration platform:

- **Patients**: Seamless self-registration, profile management, medical history, and lab report tracking.
- **Appointments**: Specialist directory, database-backed slot booking, rescheduling, and scheduled reminders.
- **Emergency Requests**: Rapid emergency intake and prioritized triage board.
- **Ambulance Coordination**: Recorded fleet status and location, simulated dispatch requests, assignment, and hotline information.
- **Blood Services**: Search across eight blood groups using configured inventory records, submit requirements, and review request status.
- **Healthcare Facilities**: Directory of hospitals, clinics, and diagnostic facilities with stored contact and service details.
- **Administrative Dashboard**: Database-backed appointment and emergency statistics, patient search, and triage queues.
- **AI Guidance**: Clinical-safety-guardrailed conversational assistant for intelligent administrative guidance and workflow navigation.

## Key Features

- **Patient Management**: Fast registration, patient directory search, medical consultation history, and digital diagnostic reports.
- **Appointment Management**: Doctor specialty search, date-specific time-slot reservation, cancellation/rescheduling, and scheduled follow-up alerts.
- **Emergency Coordination**: High/critical emergency intake logging with instant administrative triage status updates.
- **Ambulance Requests**: Simulated ambulance requests, stored fleet availability and last-known location, and request status tracking.
- **Blood Search & Requests**: Search stored inventory across 8 blood groups (A+, A-, B+, B-, AB+, AB-, O+, O-) and submit requirement requests.
- **Healthcare Facility Directory**: Search facilities by type and view stored addresses, services, and contact information.
- **Dashboard & Statistics**: Administrative overview with appointment metrics, emergency statistics, patient records, and triage queues.
- **AI Assistant**: Conversational agent powered by Gemini with deterministic safety fallbacks, multi-turn context, and structured hospital tool executions.

## Safety

> **ClinicCare is an administrative and healthcare coordination platform. It does not provide medical diagnosis, treatment recommendations, prescriptions, or medical decision-making.**

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, TanStack Query (React Query), React Router v6, Lucide React, Recharts.
- **Backend**: Python 3.11, FastAPI, Pydantic v2, Pydantic Settings, SQLAlchemy 2.0, Uvicorn, Passlib (Bcrypt), Python-JOSE (JWT).
- **Database / Data Layer**: SQLite (default local development and testing), PostgreSQL 15 schema support for production deployment.
- **AI / LLM Layer**: Google Gemini (`google-generativeai`) with built-in medical safety interceptors and deterministic fallback engine.
- **Automation & Integrations**: Meta WhatsApp Cloud API webhooks, AI Voice Callback requests, SMTP error alerting, n8n workflow definitions.


## Architecture

- **Frontend**: Single-page application built with React 18, TypeScript, and Vite. Utilizes Tailwind CSS for responsive styling, TanStack Query for server-state caching and synchronization, and Recharts for administrative visual analytics.
- **Backend**: High-performance RESTful API built on FastAPI and Python 3.11 with Pydantic v2 schemas for strict data validation and serialization.
- **Database / Data Layer**: Relational data persistence powered by SQLAlchemy 2.0 ORM. Supports SQLite for rapid local testing and development, and PostgreSQL 15 for containerized and production environments across 15 domain models.
- **AI / Assistant Layer**: Autonomous healthcare AI assistant powered by Google Gemini with strict medical safety guardrails, clinical emergency redirection, and structured tool calling for administrative lookup.
- **External Integrations**: Meta WhatsApp Cloud API webhook receiver for automated reminders, AI Voice Callback requests, SMTP error notifications, and n8n orchestration workflows.

## Project Structure

```text
ClinicCare/
├── backend/
│   ├── app/
│   │   ├── ai/              # AI provider (Gemini), tool definitions, safety guardrails
│   │   ├── api/             # FastAPI routers (auth, appointments, ambulances, blood, facilities, etc.)
│   │   ├── core/            # Configuration settings and JWT security helpers
│   │   ├── db/              # SQLAlchemy session setup, base models, and seed script
│   │   ├── integrations/    # WhatsApp Meta Cloud API and external communication handlers
│   │   ├── models/          # 15+ SQLAlchemy database domain models
│   │   ├── schemas/         # Pydantic request/response data models
│   │   ├── services/        # Core business logic and database transaction services
│   │   └── main.py          # FastAPI application entry point, CORS, and health check
│   ├── tests/               # Pytest automated test suite (47 verified tests)
│   ├── Dockerfile           # Production container configuration for Cloud Run
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components, layout sidebars, modals, navigation
│   │   ├── context/         # AuthContext and ToastContext state management
│   │   ├── pages/           # Patient & Admin pages (Appointments, Ambulances, Blood, Facilities, Chat)
│   │   ├── services/        # Axios API client modules
│   │   ├── types/           # TypeScript interface definitions
│   │   ├── App.tsx          # Client-side routing and protected routes
│   │   └── main.tsx         # React root entry point
│   ├── Dockerfile           # Multi-stage production Nginx container build
│   └── package.json         # Frontend dependencies and Vite build scripts
├── database/
│   ├── schema.sql           # Complete PostgreSQL DDL schema definition
│   └── README.md            # Schema setup and migration notes
├── docs/
│   ├── ARCHITECTURE.md      # Detailed architectural diagrams and specifications
│   ├── AI_SAFETY_GUARDRAILS.md # Clinical safety rules and fallback guidelines
│   └── API_DOCUMENTATION.md # REST API endpoint reference
├── n8n/
│   ├── workflows/           # JSON automation workflow definitions
│   └── README.md            # n8n workflow setup documentation
├── docker-compose.yml       # Multi-service local orchestrator (Postgres, Redis, Backend, Frontend, n8n)
├── .env.example             # Master environment configuration template
└── README.md                # Project documentation
```

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Server: `http://127.0.0.1:8000`
- API Health Check: `http://127.0.0.1:8000/health`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

- Web Application: `http://127.0.0.1:5173`

The login screen's **Quick Demo Logins** fill seeded demonstration accounts. Use them only with an isolated development database; configure unique credentials for any shared deployment.


## Environment Variables

The backend configuration is managed through `backend/app/core/config.py` and loaded from environment variables or a `.env` file based on `.env.example`.

Key configurable environment variables include:
- `PROJECT_NAME`: Platform title ("ClinicCare").
- `ENVIRONMENT`: Runtime environment (`development` / `production`).
- `PORT`: Web server port (Cloud Run sets this dynamically, default `8000`).
- `HOST`: Server interface binding (`0.0.0.0`).
- `CORS_ORIGINS`: JSON list or comma-separated allowed origin URLs.
- `JWT_SECRET`: Minimum 32-character secret key for cryptographic token signing.
- `AUTOMATED_WORKFLOW_KEY`: Optional shared secret for configured n8n-to-backend workflow requests.
- `N8N_BASIC_AUTH_PASSWORD`: n8n sign-in password when running the Compose stack.
- `DATABASE_URL`: Relational database connection string (`sqlite:///./hospital.db` or `postgresql://...`).
- `GEMINI_API_KEY`: Google Gemini API key for conversational AI assistance.
- `WA_PHONE_NUMBER_ID` & `WA_ACCESS_TOKEN`: Meta WhatsApp Cloud API credentials.
- `EMAIL_PROVIDER`: Email dispatch transport (`brevo` for free tier with individual sender verification, `resend` for custom domains, or `smtp`).
- `BREVO_API_KEY`: Secret API key for Brevo HTTPS API (e.g. `xkeysib-...`).
- `BREVO_SENDER_EMAIL`: Verified sender email address in Brevo (e.g. `yourname@gmail.com`).
- `BREVO_SENDER_NAME`: Sender display name (defaults to `ClinicCare Healthcare`).
- `GOOGLE_CLIENT_ID`: Google OAuth 2.0 Client ID for backend token verification.
- `VITE_GOOGLE_CLIENT_ID`: Google OAuth 2.0 Client ID for frontend Google Identity Services button.
- `VITE_API_BASE_URL`: Frontend API base URL (defaults to `https://cliniccare-backend-48g6.onrender.com/api` in production).

*(Never commit `.env` or production credentials to source control).*

### Email & OTP Delivery Architecture

ClinicCare supports two modern HTTPS API email transports running over standard port 443 (avoiding SMTP port 587 timeouts on Render):

#### Solution A: Brevo (Sendinblue) HTTPS API — Free Tier Without Custom Domain
If you do not own a custom domain and do not want to purchase one or configure DNS records, **Brevo** provides a permanent free tier allowing you to verify an individual sender email (such as a personal `@gmail.com`) and send OTP emails to **any recipient**:

1. **Free Tier Highlights**:
   - **300 free emails per day** (9,000/month) forever.
   - **No custom domain required**: Verify an individual mailbox via confirmation link.
   - **Delivers to any email address**: Developer, friends, external patient test accounts.
   - **HTTPS REST API over port 443**: Fully compatible with Render's network policies.
2. **Setup Steps**:
   - Create a free account at [brevo.com](https://www.brevo.com).
   - Go to **Senders & IPs** > **Senders** > **Add a sender**.
   - Enter your name and email address (e.g. `yourname@gmail.com`).
   - Click the confirmation link sent to your inbox. The sender status will change to **Verified**.
   - Go to **SMTP & API** > **API Keys** and generate a new key (`xkeysib-...`).
3. **Configure Render Backend**:
   In your Render Dashboard for `cliniccare-backend`:
   - `EMAIL_PROVIDER` = `brevo`
   - `BREVO_API_KEY` = `xkeysib-...`
   - `BREVO_SENDER_EMAIL` = `yourname@gmail.com`
   - `BREVO_SENDER_NAME` = `ClinicCare Healthcare`

#### Solution B: Resend HTTPS API — Custom Domain Delivery
If you own a custom domain with DNS control:
1. Set `EMAIL_PROVIDER=resend`.
2. Add `RESEND_API_KEY` in Render.
3. Verify your domain at [resend.com/domains](https://resend.com/domains) by adding DKIM, SPF, and DMARC DNS records.
4. Set `RESEND_FROM_EMAIL=ClinicCare Healthcare <alerts@yourverifieddomain.com>`.

*(Note: Without a verified custom domain, Resend sandbox with `onboarding@resend.dev` restricts delivery exclusively to the Resend account owner with HTTP 403).*

### Google Sign-In Setup (Google Identity Services)

ClinicCare supports one-click patient authentication via official Google Identity Services (GSI) OAuth 2.0:

1. **Google Cloud Console Setup**:
   - Navigate to [Google Cloud Console](https://console.cloud.google.com).
   - Create or select your Google Cloud project.
   - Go to **APIs & Services** > **OAuth consent screen**.
     - Set User Type to **External**.
     - Fill App Name (`ClinicCare`), User support email, and Developer contact email.
     - Add required scopes: `openid`, `email`, `profile`.
   - Go to **APIs & Services** > **Credentials** > **Create Credentials** > **OAuth Client ID**.
     - Application type: **Web application**.
     - Name: `ClinicCare Web Client`.
     - **Authorized JavaScript origins**:
       - `https://cliniccare-g3c6.onrender.com` (Production frontend)
       - `http://localhost:5173` (Local frontend dev)
       - `http://localhost:3000`
     - Click **Create** and copy your **Client ID** (e.g., `123456789-xxxx.apps.googleusercontent.com`).
2. **Configure in Render**:
   - **Frontend Service (`cliniccare-g3c6`)**:
     Add environment variable: `VITE_GOOGLE_CLIENT_ID` = `<your-google-client-id>`.
   - **Backend Service (`cliniccare-backend-48g6`)**:
     Add environment variable: `GOOGLE_CLIENT_ID` = `<your-google-client-id>`.
3. **Security Safeguards**:
   - Backend independently verifies token signature, expiration, issuer (`accounts.google.com`), and audience with Google.
   - Requires `email_verified=True`.
   - New Google users are strictly registered with `PATIENT` role (never elevates to Admin or Doctor).
   - Existing accounts resolve cleanly by normalized email without account duplication or password overwrites.

## Testing

Run the automated backend test suite with:

```powershell
cd backend
pytest -v
```

**Verified Test Result**:
- `129 passed`; one third-party deprecation warning. Full suite passing across all clinical, auth, billing, phase 1-4, and Resend HTTPS integration tests.

Frontend production build verification:

```powershell
cd frontend
npm run build
```

**Verified Build Result**:
- Production bundle compiled with no TypeScript/build errors. Vite reports a JavaScript chunk-size warning.

## Deployment

### Google Cloud Run (Not Deployed)

The backend Dockerfile runs `uvicorn app.main:app` on `0.0.0.0` and uses Cloud Run's `PORT` (default `8000`). The `/health` endpoint checks the database connection. Docker and Google Cloud CLI deployment were not available or verified in this workspace.

Create the required Secret Manager secrets for `DATABASE_URL` and `JWT_SECRET`, then run the following with an authenticated Google Cloud CLI and an Artifact Registry repository:

```bash
# Select the project and region, then build the existing backend image.
gcloud config set project PROJECT_ID
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT_ID/cliniccare/cliniccare-backend ./backend

# Deploy with database and signing credentials sourced from Secret Manager.
gcloud run deploy cliniccare-backend \
  --image REGION-docker.pkg.dev/PROJECT_ID/cliniccare/cliniccare-backend \\
  --platform managed \
  --region REGION \\
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,CORS_ORIGINS=https://FRONTEND_URL \\
  --set-secrets DATABASE_URL=cliniccare-database-url:latest,JWT_SECRET=cliniccare-jwt-secret:latest

# Build the frontend with the deployed API base URL if hosted separately.
cd frontend
VITE_API_BASE_URL="https://BACKEND_URL/api" npm run build
```

The frontend can also be deployed as its existing Nginx container. Configure `VITE_API_BASE_URL` at image build time and set backend CORS origins for the deployed frontend.

## Demo Flow

1. **Register / Search Patient**: Register a synthetic patient or use a seeded role's Quick Demo Login button.
2. **Book Appointment**: Choose a clinical specialty, select an available doctor and time slot, and confirm the consultation booking.
3. **Show Appointment Status**: Access *My Appointments* to verify scheduled status, download details, or reschedule.
4. **Demonstrate Emergency Request**: Submit an emergency intake request and view immediate high-priority triage confirmation.
5. **Demonstrate Ambulance Request**: Request an emergency BLS/ALS ambulance, check available fleet vehicles, and view simulated route dispatch.
6. **Search Blood Availability**: Filter across 8 blood groups (e.g. `O-`, `A+`) and locate available units across hospital blood banks.
7. **Submit Blood Requirement**: Submit an urgent patient blood requirement ticket with required units.
8. **Show Nearby Healthcare Facility**: Browse stored hospital, clinic, and diagnostic facility records and their contact information.
9. **Show Admin Dashboard**: Use the seeded Admin Quick Demo Login to view appointment and emergency statistics, patient search, and coordination queues.
10. **Ask AI Assistant**: Ask questions in *AI Health Assistant* (e.g. `"What is ClinicCare?"`, `"Which doctors are available?"`, `"Where is the blood bank?"`) to see safety guardrails and autonomous guidance.

