from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.lab import LabReport, LabOrder
from app.models.clinical import ConsultationRecord
from app.models.user import Patient, Doctor
from app.services.audit_service import audit_service


class ClinicalAIService:
    @staticmethod
    def draft_consultation_note(
        db: Session,
        patient_id: str,
        doctor_id: str,
        clinic_id: str,
        raw_notes: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """
        AI Clinical Drafting Assistant:
        Generates a structured consultation draft from authorized notes.
        CRITICAL GUARDRAIL:
        - Output is strictly a DRAFT.
        - AI NEVER autonomously prescribes or diagnoses.
        - Attending physician review and manual authorization is mandatory.
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        # Extract structured intent from physician notes
        lines = [l.strip() for l in raw_notes.split("\n") if l.strip()]
        chief_complaint = lines[0] if lines else "Patient clinical presentation review"
        hpi = " ".join(lines[1:]) if len(lines) > 1 else raw_notes

        draft = {
            "chief_complaint": chief_complaint,
            "history_of_present_illness": hpi,
            "examination_notes": "Awaiting physical evaluation by attending physician.",
            "suggested_differential_diagnosis": "Clinical correlation recommended based on detailed examination.",
            "treatment_plan_draft": "Symptomatic management; confirm drug allergies and renal function before finalizing pharmacotherapy.",
            "is_ai_draft": True,
            "requires_human_verification": True,
            "disclaimer": "AI-generated draft for physician review only. Does NOT constitute a finalized diagnosis or prescription. Attending physician must review, modify, and authorize.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "author_id": actor_id,
        }

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="AI_CLINICAL_DRAFT_GENERATE",
            entity_type="ConsultationDraft",
            entity_id=patient_id,
            details={"patient_id": patient_id, "notes_len": len(raw_notes)}
        )

        return draft

    @staticmethod
    def summarize_lab_report(
        db: Session,
        order_id: str,
        clinic_id: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """
        AI Lab Report Summarizer:
        Provides a concise, non-diagnostic overview of released lab results for authorized users.
        CRITICAL GUARDRAILS:
        - Only released reports can be summarized.
        - Prefaced with mandatory disclaimer.
        - Does NOT invent missing values or formulate diagnostic conclusions.
        """
        order = db.query(LabOrder).filter(
            LabOrder.id == order_id,
            LabOrder.clinic_id == clinic_id
        ).first()
        if not order:
            raise ValueError("Lab order not found or unauthorized")

        if not order.report or not order.report.is_released:
            raise ValueError("Cannot summarize unreleased lab report. Results must be validated by a pathologist first.")

        # Aggregate parameters
        abnormal_items = []
        normal_items = []
        for r in order.results:
            param_str = f"{r.parameter_name}: {r.result_value} {r.unit or ''} (Ref: {r.reference_range or 'N/A'})"
            if r.is_abnormal:
                abnormal_items.append(param_str)
            else:
                normal_items.append(param_str)

        summary_text = (
            "AI-generated summary. Please review the original report.\n\n"
            f"Laboratory Order: {order.order_number}\n"
            f"Report Number: {order.report.report_number}\n"
        )

        if abnormal_items:
            summary_text += "\nFlagged Values Requiring Clinical Attention:\n- " + "\n- ".join(abnormal_items) + "\n"
        else:
            summary_text += "\nAll recorded parameters are within biological reference ranges.\n"

        if order.report.summary_notes:
            summary_text += f"\nPathologist Impression:\n{order.report.summary_notes}\n"

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="AI_REPORT_SUMMARY_GENERATE",
            entity_type="LabReport",
            entity_id=order.report.id,
            details={"order_number": order.order_number, "abnormal_count": len(abnormal_items)}
        )

        return {
            "order_number": order.order_number,
            "report_number": order.report.report_number,
            "summary": summary_text,
            "abnormal_parameters": abnormal_items,
            "disclaimer": "AI-generated summary. Please review the original report.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


clinical_ai_service = ClinicalAIService()
