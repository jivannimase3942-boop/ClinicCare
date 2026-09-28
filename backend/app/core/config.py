import os
import secrets
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ClinicCare"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "https://cliniccare-g3c6.onrender.com",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Security & JWT
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database (Supabase / Postgres / SQLite)
    DATABASE_URL: str = "sqlite:///./hospital.db"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # AI Configuration (Gemini / OpenAI)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: Optional[str] = None

    # WhatsApp Cloud API (Meta)
    WA_PHONE_NUMBER_ID: str = ""
    WA_ACCESS_TOKEN: str = ""
    WA_VERIFY_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    WA_API_VERSION: str = "v19.0"

    # Voice Calling API (External Provider: ElevenLabs / Retell / Bland AI / Twilio)
    VOICE_API_URL: Optional[str] = None
    VOICE_API_KEY: Optional[str] = None
    VOICE_AGENT_ID: Optional[str] = None

    # Email & Alerts (SMTP / SendGrid / Postmark)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_SENDER: str = "alerts@cliniccarehospital.com"
    ALERT_EMAIL_TO: str = "admin@cliniccarehospital.com"

    # Hospital Info Defaults
    HOSPITAL_NAME: str = "ClinicCare Multispeciality Hospital"
    HOSPITAL_PHONE: str = "+1 (800) 555-0199"
    HOSPITAL_EMAIL: str = "care@cliniccarehospital.com"
    HOSPITAL_ADDRESS: str = "100 Healthcare Boulevard, Suite 400, Medical District"
    EMERGENCY_HOTLINE: str = "911 / 112"

    # n8n Automation Engine
    N8N_HOST: str = "localhost"
    N8N_PORT: int = 5678
    N8N_BASIC_AUTH_USER: str = "admin"
    AUTOMATED_WORKFLOW_KEY: str = Field(default_factory=lambda: "cliniccare-internal-workflow-key-v1")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

