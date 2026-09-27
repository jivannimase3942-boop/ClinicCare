# ClinicCare Medical AI Safety & Clinical Guardrails

## Core Safety Principles

1. **Non-Diagnostic Rule**: The AI assistant never renders formal clinical diagnoses or prescribes medications.
2. **Emergency Redirection**: If severe symptoms (e.g., severe chest pain, shortness of breath, loss of consciousness, stroke symptoms, uncontrolled bleeding) are detected:
   - Sets `is_emergency = true`.
   - Generates emergency helpline numbers (108 / Emergency Room).
   - Automatically files a High-Priority front desk escalation ticket.
3. **Clinical Advice Interception**: Direct inquiries asking for prescriptions, drug dosages, or symptom diagnoses are gently intercepted with clinical disclaimers and recommendations to book an in-person doctor consultation.
4. **Autonomous Tool Calling**: The AI leverages structured function calls to query database records (e.g., finding available slots, booking appointments, looking up report readiness) strictly through validated service layers.
5. **Fail-Safe Fallback**: If LLM API keys are omitted or rate-limited, the system seamlessly activates deterministic pattern matchers and tool executors without crashing.
