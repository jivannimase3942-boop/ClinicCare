import re
from typing import Tuple

EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe", "difficulty breathing",
    "severe bleeding", "bleeding heavily", "unconscious", "unconsciousness", "fainted",
    "stroke", "paralysis", "head trauma", "severe burn", "poisoning", "seizure",
    "choking", "coughing blood", "vomiting blood", "suicide", "overdose",
    "dil ka daura", "saans lene me dikkat", "khoon beh raha hai", "behosh"
]

MEDICAL_DIAGNOSIS_KEYWORDS = [
    "what medicine should i take", "prescribe", "dosage", "how many mg",
    "what disease do i have", "diagnose me", "am i sick with", "what drug should i take",
    "cure my", "treatment for my disease", "treat my condition"
]


class MedicalSafetyGuard:
    @staticmethod
    def check_emergency(user_message: str) -> Tuple[bool, str]:
        lower_msg = user_message.lower()
        for kw in EMERGENCY_KEYWORDS:
            if kw in lower_msg:
                emergency_notice = (
                    "⚠️ **EMERGENCY DETECTED**: If you or someone around you is experiencing a medical emergency "
                    "(such as chest pain, serious breathing difficulty, severe bleeding, or unconsciousness), "
                    "please call **911 / 112** immediately or proceed to the nearest Hospital Emergency OPD.\n\n"
                    "I have automatically escalated this to our emergency front-desk staff."
                )
                return True, emergency_notice
        return False, ""

    @staticmethod
    def check_clinical_advice(user_message: str) -> Tuple[bool, str]:
        lower_msg = user_message.lower()
        for kw in MEDICAL_DIAGNOSIS_KEYWORDS:
            if kw in lower_msg:
                notice = (
                    "🩺 **Medical Safety Notice**: I can help with appointments, hospital services, ambulance coordination, "
                    "blood information, and other administrative tasks. I cannot diagnose medical conditions or recommend treatment. "
                    "Please consult one of our qualified physicians. Would you like to book an appointment?"
                )
                return True, notice
        return False, ""

