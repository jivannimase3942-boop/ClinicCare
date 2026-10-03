import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Query, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import engine, SessionLocal, Base, get_db
import app.db.base  # ensure all models are registered with Base metadata
from app.services.error_service import error_service
from app.integrations.whatsapp.service import whatsapp_service

from app.api.routes import (
    auth,
    doctors,
    departments,
    appointments,
    reports,
    feedback,
    ai,
    voice,
    escalations,
    whatsapp,
    admin,
    doctor_portal,
    ambulances,
    blood,
    facilities,
    patients,
    emergencies,
    reminders,
    clinics,
    billing,
    clinical,
    prescriptions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables if SQLite or fresh DB
    Base.metadata.create_all(bind=engine)
    try:
        from app.db.seed import seed_database
        seed_database()
        print("[ClinicCare] Database initialized and verified with seed data.")
    except Exception as e:
        print(f"[ClinicCare] Warning during seed_database in lifespan: {e}")
    yield


app = FastAPI(
    title="ClinicCare Hospital Automation API",
    description="Production-Ready ClinicCare AI Automation Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware with explicit production frontend and development origins
cors_origins = [
    "https://cliniccare-g3c6.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]
if isinstance(settings.CORS_ORIGINS, list):
    for origin in settings.CORS_ORIGINS:
        if origin not in cors_origins and origin != "*":
            cors_origins.append(origin)
elif isinstance(settings.CORS_ORIGINS, str) and settings.CORS_ORIGINS != "*":
    for origin in settings.CORS_ORIGINS.split(","):
        o = origin.strip()
        if o and o not in cors_origins:
            cors_origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for consistent structured error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else "Request error",
            "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}",
            "details": exc.detail if not isinstance(exc.detail, str) else None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    stack = traceback.format_exc()
    print(f"[UNHANDLED ERROR] {exc}\n{stack}")

    # Log to DB error_logs
    try:
        db = SessionLocal()
        error_service.log_error(
            db=db,
            message=str(exc),
            service_name="backend-api",
            error_level="CRITICAL",
            stack_trace=stack,
            endpoint=str(request.url.path),
            context={"method": request.method, "client": request.client.host if request.client else None},
        )
        db.close()
    except Exception as log_err:
        print(f"Error logging failed: {log_err}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred. Please try again later.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# Root & Health Endpoints
@app.get("/", tags=["Root"])
def root_endpoint():
    return {
        "success": True,
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_docs_url": "/docs",
    }


@app.get("/api", tags=["Root"])
def api_root_endpoint():
    return {
        "success": True,
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/api/health", tags=["Health"])
def api_health_check():
    return health_check()


@app.get("/health", tags=["Health"])
def health_check():
    db_status = "healthy"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "success": True,
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "gemini_ai_configured": bool(settings.GEMINI_API_KEY),
        "whatsapp_configured": bool(settings.WA_PHONE_NUMBER_ID and settings.WA_ACCESS_TOKEN),
    }


# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(escalations.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(doctor_portal.router, prefix="/api")
app.include_router(ambulances.router, prefix="/api")
app.include_router(blood.router, prefix="/api")
app.include_router(facilities.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(emergencies.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(clinics.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(clinical.router, prefix="/api")
app.include_router(prescriptions.router, prefix="/api")

# Direct Webhook endpoints matching JSON specification (/whatsapp-webhook)
@app.get("/whatsapp-webhook", tags=["WhatsApp Webhook"])
def verify_whatsapp_webhook_root(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    from app.integrations.whatsapp.service import whatsapp_service
    from fastapi import Response
    valid, challenge = whatsapp_service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if valid and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@app.post("/whatsapp-webhook", tags=["WhatsApp Webhook"])
async def receive_whatsapp_webhook_root(request: Request, db: Session = Depends(get_db)):
    from app.integrations.whatsapp.service import whatsapp_service
    payload = await request.json()
    result = await whatsapp_service.process_incoming_message(db, payload)
    return {"status": "EVENT_RECEIVED", "detail": result}


@app.post("/report-ready-webhook", tags=["Reports"])
async def receive_report_ready_webhook_root(request: Request, db: Session = Depends(get_db)):
    from app.services.report_service import report_service
    result = report_service.scan_and_send_report_notifications(db)
    return {"status": "SUCCESS", "detail": result}


