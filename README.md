# ClinicCare

ClinicCare is a clinic appointment, patient, and emergency coordination system built for the FIT-FEST project. It combines patient-facing workflows with administrative tools using a React frontend and a FastAPI backend.

## Problem

Clinics need a straightforward way to coordinate patient registration, appointments, emergency requests, ambulance availability, blood requirements, and facility information.

## Solution

ClinicCare provides those workflows through a shared web application, backed by REST APIs and a relational database. AI assistance uses configured providers when available and existing deterministic responses otherwise.

## Key Features

- Patient registration, profile information, directory search, and appointment history.
- Appointment booking, scheduling, status tracking, and follow-up reminders.
- Administrative dashboard, appointment coordination, and emergency statistics.
- Emergency request intake and an administrative triage board.
- Ambulance request, fleet availability, request status, assignment, and recorded location.
- Blood group search, bank directory, requirement requests, and request management.
- Healthcare facility search and information directory.
- AI assistant for administrative and service-navigation questions, with safety guardrails.

Demo records are not live clinical, inventory, location, or dispatch data.

## FIT-FEST Requirements

The project includes patient registration and search; appointment booking, status, history, and reminders; clinic administration and statistics; emergency request management; ambulance requests and fleet status; blood search and request management; facility search; and AI service guidance. Feature behavior depends on the configured database and integrations.

> ClinicCare is an administrative and healthcare coordination platform. It does not provide medical diagnosis, treatment recommendations, prescriptions, or medical decision-making.

## Technology Stack

- Frontend: React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query.
- Backend: Python 3.11, FastAPI, Pydantic, SQLAlchemy.
- Database: SQLite for local development; PostgreSQL is configured for Docker Compose.
- Optional integrations: Gemini, WhatsApp, voice provider, SMTP, Redis, and n8n.

## Project Structure

```text
backend/       FastAPI application, services, models, and tests
frontend/      React application and Vite build
database/      SQL schema and database notes
docs/          Architecture, API, and safety documentation
n8n/           Workflow definitions
```

## Environment Variables

`backend/app/core/config.py` defines the backend settings. Copy `.env.example` to `backend/.env` for local backend configuration. Docker Compose reads a root `.env` file; copy the template there and replace the placeholder values before starting containers. Do not commit either file.

Common settings include `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `PORT`, and optional integration keys such as `GEMINI_API_KEY`. Docker Compose also requires `POSTGRES_PASSWORD`, `JWT_SECRET`, and `N8N_BASIC_AUTH_PASSWORD`. `VITE_API_BASE_URL` defaults to `/api` in the production frontend image; set it to the deployed backend API URL when frontend and backend are hosted separately.

## Local Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API health endpoint is `http://127.0.0.1:8000/health` and API documentation is at `/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Vite serves the application at `http://127.0.0.1:5173`. The default frontend API URL is `http://localhost:8000/api`; override it with `VITE_API_BASE_URL` when needed.

## Testing

```powershell
cd backend
pytest -q
cd ..\frontend
npm run build
```

`run_live_e2e_verification.py` starts local services and runs the Playwright browser flow; Playwright and its Chromium browser must be installed.

## Deployment

The backend Docker image runs `uvicorn app.main:app`, binds to `0.0.0.0`, and uses `PORT` (default `8000`). It exposes `/health`. The frontend image accepts `VITE_API_BASE_URL` at build time. Keep credentials in deployment secret settings and use a managed database for persistent production data.

### Docker Compose

Set the required values in the root `.env`, then run:

```powershell
docker compose up --build
```

### Cloud Run

The backend container is configured for Cloud Run's `PORT` contract. Configure `DATABASE_URL`, a strong `JWT_SECRET`, allowed `CORS_ORIGINS`, and any required integration secrets in Cloud Run. Deploy the frontend separately or configure its build with the backend API URL. Cloud Run deployment has not been executed or verified from this repository workspace.

## Demo Flow

1. Register a synthetic patient or use a seeded demo role from the login screen.
2. Browse doctors and book an available appointment slot.
3. Search blood inventory and facilities; submit clearly identified test requests only.
4. Review the patient and request records in the administrative dashboard.
5. Ask the AI assistant how to navigate appointment, ambulance, blood, and facility workflows.

## Limitations

- Facility, inventory, ambulance availability, and response-time values may be seeded or simulated; they are not live operational feeds.
- External AI and messaging integrations require valid provider configuration; deterministic AI responses are available for supported administrative prompts.
- Cloud deployment, production database provisioning, and third-party integrations require environment-specific credentials and have not been verified here.

