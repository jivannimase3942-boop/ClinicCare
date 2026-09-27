import json
import re
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.ai import tools
from app.models.user import Doctor, Department, Patient


from app.ai.medications import MEDICATION_DATABASE, lookup_medication


def format_doctor_name(name: str) -> str:
    clean = name.strip()
    if clean.lower().startswith("dr."):
        return clean
    elif clean.lower().startswith("dr "):
        return f"Dr. {clean[3:].strip()}"
    return f"Dr. {clean}"


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_chat_response(
        self,
        db: Session,
        patient_id: Optional[str],
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        pass


class RuleBasedFallbackProvider(BaseAIProvider):
    """
    Intelligent NLP intent matching & tool runner for standalone operation
    without external API keys, supporting English, Hindi, and Hinglish.
    """
    def generate_chat_response(
        self,
        db: Session,
        patient_id: Optional[str],
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        msg = user_message.lower().strip()
        tool_executions = []
        intent = "general_inquiry"
        reply = ""
        suggested_actions = ["Check Doctors", "Book Appointment", "Check Report Status", "Request Call"]

        # 0. About ClinicCare Platform
        if any(w in msg for w in ["what is cliniccare", "about cliniccare", "who are you", "what does cliniccare do", "what is this platform", "what is carepulse", "about this app", "kya hai cliniccare"]):
            intent = "about_cliniccare"
            reply = (
                f"🏥 **Welcome to ClinicCare**\n\n"
                f"**ClinicCare** is an intelligent healthcare administrative and hospital automation platform designed to streamline patient care, clinician scheduling, and emergency workflows.\n\n"
                "**Core Integrated Capabilities:**\n"
                "• 📅 **Appointment Management**: Specialist discovery, real-time slot scheduling, rescheduling, and cancellation.\n"
                "• 🚑 **Emergency & Ambulance Dispatch**: 24/7 BLS/ALS ambulance fleet tracking and rapid dispatch triage.\n"
                "• 🩸 **Blood Services**: Real-time 8 blood group inventory search, requirement request posting, and blood bank matching.\n"
                "• 🏥 **Healthcare Facilities**: City-wide directory of trauma centers, specialized clinics, and diagnostic labs.\n"
                "• 📄 **Diagnostic Lab Reports**: Pathology and diagnostic report status tracking with digital ready notices.\n"
                "• 🔔 **Follow-Up Reminders**: Scheduled reminders and automated notification dispatch.\n\n"
                "🛡️ **Medical Safety Boundary**:\n"
                "ClinicCare is an administrative coordination system. It does **not** provide clinical medical diagnosis, personalized treatment recommendations, or drug prescriptions."
            )
            suggested_actions = ["Book Appointment", "Request Ambulance", "Search Blood", "Find Facilities"]

        # 1. Voice Call Request
        if any(w in msg for w in ["call me", "request call", "phone call", "voice call", "mujhe call karo", "call kijiye"]):
            intent = "request_voice_call"
            phone_match = re.search(r'(\+?\d{10,13})', msg)
            phone = phone_match.group(1) if phone_match else None

            if patient_id and not phone:
                p = db.query(Patient).filter(Patient.id == patient_id).first()
                if p and p.user and p.user.phone:
                    phone = p.user.phone

            if not phone:
                phone = "Not provided (Online Patient)"

            if patient_id:
                res = tools.request_ai_voice_call(db, patient_id, phone, reason=user_message)
                tool_executions.append({"tool_name": "request_ai_voice_call", "parameters": {"phone": phone, "reason": user_message}, "result": res})
                reply = f"📞 I have submitted your request for an AI voice call to **{phone}**. Our system will initiate the call shortly."
            else:
                reply = "📞 To request a voice call, please log in so we can connect you with your registered phone number."

        # 2. Report Status Check
        elif any(w in msg for w in ["report", "test result", "lab report", "meri report", "blood test result", "xray result"]):
            intent = "check_report_status"
            if patient_id:
                res = tools.check_my_report_status(db, patient_id)
                tool_executions.append({"tool_name": "check_my_report_status", "parameters": {"patient_id": patient_id}, "result": res})
                reports = res.get("reports", [])
                if not reports:
                    reply = "📄 You currently have no diagnostic reports on file."
                else:
                    reply = f"📄 **Found {len(reports)} Report(s) on your record:**\n"
                    for r in reports:
                        status_badge = f"**[{r['status'].upper()}]**"
                        reply += f"- **{r['title']}** ({r['type']}): {status_badge} - Date: {r['date']} (Dr. {r['doctor'] or 'Specialist'})\n"
                    reply += "\nYou can view and download ready reports in your **Reports** tab."
            else:
                reply = "📄 To check your personal medical reports, please sign in to your patient account."

        # 3. Human / Front-Desk Escalation
        elif any(w in msg for w in ["front desk", "talk to front desk", "speak to staff", "customer support", "escalate", "helpdesk", "reception", "complaint", "billing query", "human agent", "talk to human", "speak with human"]):
            intent = "escalate_to_front_desk"
            if patient_id:
                res = tools.escalate_to_front_desk(
                    db=db,
                    patient_id=patient_id,
                    reason="patient_requested_call",
                    priority="medium",
                    notes=user_message,
                    conversation_id=conversation_id
                )
                tool_executions.append({"tool_name": "escalate_to_front_desk", "parameters": {"reason": "patient_requested_call"}, "result": res})
                reply = "👨💼 I have transferred your request to our **Hospital Front Desk Team** (Escalation Ticket created). A patient care coordinator will assist you shortly."
            else:
                reply = f"👨💼 You can reach our Front Desk reception directly at **{settings.HOSPITAL_PHONE}** or email **{settings.HOSPITAL_EMAIL}**. Address: {settings.HOSPITAL_ADDRESS}."

        # 4. Medication & Drug Information Inquiries (Educational Info + Strict Medical Safety Guard)
        elif any(med in msg for med in MEDICATION_DATABASE.keys()) or any(w in msg for w in ["tell me about", "what is", "information on", "side effects of", "medicine", "tablet", "capsule", "drug"]):
            matched_med = lookup_medication(msg)
            if matched_med:
                intent = "medication_info"
                reply = (
                    f"💊 **{matched_med['name']} Overview**\n\n"
                    f"• **Pharmacological Class**: {matched_med['class']}\n"
                    f"• **Primary Uses**: {matched_med['uses']}\n"
                    f"• **Mechanism of Action**: {matched_med['mechanism']}\n"
                    f"• **Important Precaution**: {matched_med['precaution']}\n\n"
                    f"🩺 **Strict Medical Safety Notice**:\n"
                    f"This information is provided solely for educational purposes. As an AI assistant, I cannot prescribe medications, determine personal dosages, or replace physician guidance. "
                    f"Please consult a specialist in our **{matched_med['department']}** department before taking any medication.\n\n"
                    f"Would you like me to help you book a consultation with one of our specialists?"
                )
                suggested_actions = ["Book Appointment", "Check Doctors", "Talk to Front Desk"]
            else:
                intent = "general_medication_query"
                reply = (
                    "💊 **Medication & Clinical Guidance**\n\n"
                    "Our hospital pharmacy and clinical specialists provide verified pharmaceutical care. "
                    "As an AI assistant, I can provide general educational drug overviews, but I strictly cannot prescribe medications or provide individualized dosage advice.\n\n"
                    "Please let me know the name of the medication you'd like educational information about, or let me know if you would like to book an appointment with our specialist physicians."
                )
                suggested_actions = ["Check Doctors", "Book Appointment", "Talk to Front Desk"]

        # 5. Cancel Appointment
        elif any(w in msg for w in ["cancel appointment", "cancel my appointment", "appointment cancel", "cancel booking", "radd"]):
            intent = "cancel_appointment"
            reply = "📅 To cancel an active appointment, please go to the **Appointments** tab in your patient portal, or let our front desk know your Appointment ID."
            suggested_actions = ["View Appointments", "Talk to Front Desk", "Check Doctors"]

        # 6. Reschedule Appointment
        elif any(w in msg for w in ["reschedule", "change time", "change date", "reschedule appointment", "time badalna"]):
            intent = "reschedule_appointment"
            reply = "🔄 To reschedule your appointment to a new date or time slot, please visit the **Appointments** tab or ask me to check doctor slot availability."
            suggested_actions = ["Check Slots", "Book Appointment", "Talk to Front Desk"]

        # 7. Slot Checking & Availability
        elif any(w in msg for w in ["slots", "available slots", "slot", "available time", "free slot", "timing slot", "show me available appointment slots"]):
            intent = "check_slots"
            doctors = db.query(Doctor).filter(Doctor.is_active == True).all()
            if doctors:
                first_doc = doctors[0]
                tomorrow = date.today() + timedelta(days=1)
                res = tools.check_doctor_booked_slots(db, first_doc.id, tomorrow)
                tool_executions.append({"tool_name": "check_doctor_booked_slots", "parameters": {"doctor_id": first_doc.id, "slot_date": tomorrow.isoformat()}, "result": res})
                reply = f"📅 **Slot Availability for Tomorrow ({tomorrow.isoformat()}):**\n\n"
                doc_title = format_doctor_name(first_doc.full_name)
                reply += f"**{doc_title}** ({first_doc.specialization} - {first_doc.department.name if first_doc.department else 'OPD'}):\n"
                avail = res.get("available_slots", [])
                if avail:
                    reply += f"• Available Slots: {', '.join(avail[:6])}\n"
                else:
                    reply += "• No open slots for tomorrow. Please check another date in the booking calendar.\n"
                reply += "\nSelect any doctor from the **Book Appointment** tab to view live slots for any date."
            else:
                reply = "📅 Please browse our **Doctors** directory to see active schedules and open consultation slots."

        # 8. Hospital Location, Address & Contact Details
        elif any(w in msg for w in ["where is the hospital", "hospital address", "hospital location", "address", "location", "timings", "contact", "phone number", "emergency number", "kahan hai", "pata"]):
            intent = "hospital_info"
            res = tools.get_hospital_doctor_info(db)
            reply = (
                f"🏥 **{res['hospital_name']}**\n\n"
                f"📍 **Address**: {res['hospital_address']}\n"
                f"📞 **Phone / Reception**: {res['hospital_phone']}\n"
                f"✉️ **Email**: {res['hospital_email']}\n"
                f"🚨 **Emergency Hotline**: {res['emergency_hotline']}\n"
                f"⏰ **OPD Consultation Hours**: 09:00 AM - 06:00 PM (Emergency open 24/7)\n\n"
                f"We have **{len(res['departments'])} specialized departments** and **{len(res['doctors'])} certified doctors** available on campus."
            )
            suggested_actions = ["Check Doctors", "Book Appointment", "Call Reception"]

        # 9. Doctor & Department Discovery
        elif any(w in msg for w in ["doctor", "doctors", "specialist", "dr.", "dr ", "physician", "surgeon", "cardiologist", "neurologist", "pediatrician", "orthopedic", "ent", "dermatologist", "oncologist", "gynecologist", "opd", "consultation fee", "department"]):
            intent = "doctor_discovery"
            res = tools.get_hospital_doctor_info(db)
            tool_executions.append({"tool_name": "get_hospital_doctor_info", "parameters": {}, "result": {"hospital": res["hospital_name"], "total_doctors": len(res["doctors"])}})
            matched_docs = []
            for doc in res["doctors"]:
                if doc["name"].lower() in msg or (doc["department"] and doc["department"].lower() in msg) or doc["specialization"].lower() in msg:
                    matched_docs.append(doc)

            if matched_docs:
                reply = f"🏥 **Matching Doctors at {res['hospital_name']}:**\n\n"
                for d in matched_docs[:4]:
                    d_title = format_doctor_name(d['name'])
                    reply += f"• **{d_title}** ({d['department']} - {d['specialization']})\n"
                    reply += f"  🎓 {d['qualification']} | ⏱️ {d['experience_years']} yrs exp\n"
                    reply += f"  💰 Fee: ₹{d['fee']:.2f} | 📅 Available: {d['available_days']} ({d['available_hours']})\n\n"
                reply += "Would you like me to book an appointment with any of these specialists?"
            else:
                reply = f"🏥 **{res['hospital_name']} - Active Specialists:**\n\n"
                for d in res['doctors'][:5]:
                    d_title = format_doctor_name(d['name'])
                    reply += f"• **{d_title}** — {d['specialization']} ({d['department']}) | Fee: ₹{d['fee']} | Days: {d['available_days']}\n"
                reply += f"\nTotal {len(res['doctors'])} doctors across {len(res['departments'])} departments. Click **Book Appointment** to select a slot!"
            suggested_actions = ["Book Appointment", "Cardiology", "Neurology", "Orthopedics"]

        # 10. How to Request an Ambulance / Dispatch Ambulance
        elif any(w in msg for w in ["how do i request an ambulance", "how to request an ambulance", "request an ambulance", "request ambulance", "ambulance request", "ambulance chahiye", "dispatch ambulance"]):
            intent = "ambulance_coordination"
            amb_info = tools.get_available_ambulances_info(db)
            tool_executions.append({"tool_name": "get_available_ambulances_info", "parameters": {}, "result": amb_info})
            reply = (
                f"🚑 **How to Request an Ambulance in ClinicCare:**\n\n"
                f"1. Open the **Ambulance** module from your top navigation or patient portal.\n"
                f"2. Fill in your **Pickup Address**, **Destination Facility**, and contact phone number.\n"
                f"3. Select the urgency level (**Medium**, **High**, or **Critical**).\n"
                f"4. Click **Dispatch Ambulance** to broadcast to our emergency dispatch team.\n"
                f"5. Track status in real time: **Requested → Assigned → En Route → Arrived**.\n\n"
                f"**Current Fleet Status:**\n"
                f"• Active Fleet: **{amb_info['available_count']} / {amb_info['total_fleet']} Ambulances Available**\n"
                f"• 24/7 Emergency Hotline: **{settings.EMERGENCY_HOTLINE}**\n\n"
                f"🚨 For life-threatening emergencies, dial **{settings.EMERGENCY_HOTLINE}** immediately."
            )
            suggested_actions = ["Request Ambulance", "Emergency 911/112", "Call Reception"]

        # 11. Ambulance Requests & Fleet Availability
        elif any(w in msg for w in ["ambulance", "emergency vehicle", "ambulance availability", "ambulance fleet"]):
            intent = "ambulance_coordination"
            amb_info = tools.get_available_ambulances_info(db)
            tool_executions.append({"tool_name": "get_available_ambulances_info", "parameters": {}, "result": amb_info})
            reply = (
                f"🚑 **ClinicCare Ambulance Coordination & Fleet Status**\n\n"
                f"• Available Active Fleet: **{amb_info['available_count']} / {amb_info['total_fleet']} Ambulances**\n"
                f"• Base Station: ClinicCare Emergency Dispatch Center\n"
                f"• Hotline: **{settings.EMERGENCY_HOTLINE}** (24/7)\n\n"
                "To request an immediate ambulance dispatch, please go to the **Ambulance** module or provide your pickup address and contact number here."
            )
            suggested_actions = ["Request Ambulance", "Emergency 911/112", "Call Dispatch Desk"]

        # 12. How to Request Blood / Submit Blood Requirement
        elif any(w in msg for w in ["how do i request blood", "how to request blood", "request blood", "blood requirement", "submit blood request", "blood requirement request"]):
            intent = "blood_requirement_request"
            reply = (
                "🩸 **How to Submit a Blood Requirement Request in ClinicCare:**\n\n"
                "1. Go to the **Blood Bank** tab in the navigation menu.\n"
                "2. Click on the **Submit Blood Requirement** tab.\n"
                "3. Fill in the **Patient Name**, required **Blood Group** (e.g. A+, B+, O+, AB-), **Units Required**, and **Hospital Location**.\n"
                "4. Select the urgency level (**Normal**, **Urgent**, or **Critical**).\n"
                "5. Click **Submit Blood Requirement Request**.\n"
                "6. Your request is immediately broadcast to hospital blood banks and administrative coordinators for matching!\n\n"
                "You can track matching status and donor bank allocations under **My Requests**."
            )
            suggested_actions = ["Blood Bank", "Submit Blood Request", "Search Blood"]

        # 13. How to Search for Blood & Blood Bank Directory
        elif any(w in msg for w in ["how can i search for blood", "how to search for blood", "how do i search for blood", "search for blood", "blood group search", "blood search", "blood bank", "blood group", "blood availability", "rakt", "khoon"]):
            intent = "blood_search"
            # Extract blood group if mentioned
            bg_match = re.search(r'\b(A\+|A-|B\+|B-|AB\+|AB-|O\+|O-)\b', user_message.upper())
            bg_target = bg_match.group(1) if bg_match else None
            b_info = tools.search_blood_units(db, blood_group=bg_target)
            tool_executions.append({"tool_name": "search_blood_units", "parameters": {"blood_group": bg_target}, "result": b_info})
            if bg_target:
                reply = f"🩸 **Blood Availability for {bg_target}:**\n\n"
            else:
                reply = (
                    "🩸 **How to Search for Blood & Inventory Overview:**\n\n"
                    "1. Open the **Blood Bank** module from the top navigation.\n"
                    "2. Filter by any of the 8 blood groups (**A+, A-, B+, B-, AB+, AB-, O+, O-**) or by city.\n"
                    "3. Review real-time verified units available, reserve status, and contact phone numbers.\n\n"
                    "**ClinicCare Blood Bank Directory & Stock:**\n\n"
                )
            if b_info["results"]:
                for r in b_info["results"][:4]:
                    reply += f"• **{r['blood_bank']}** ({r['city']}): {r['blood_group']} — **{r['units_available']} Units** ({r['status'].replace('_', ' ').capitalize()}) | 📞 {r['phone']}\n"
            else:
                reply += "Verified donor blood units available across ClinicCare Central Blood Bank and partner centers. Emergency units on standby 24/7.\n"
            reply += "\nPlease check the **Blood Bank** tab for complete city-wide stock details."
            suggested_actions = ["Check Blood Bank", "O+ Blood", "A+ Blood", "B+ Blood", "Submit Blood Request"]

        # 14. How to Find a Nearby Hospital / Clinic / Healthcare Facilities
        elif any(w in msg for w in ["how do i find a nearby hospital", "find a nearby hospital", "nearby hospital", "nearby clinic", "healthcare facilities", "find hospital", "nearby facilities", "facility search", "find nearby"]):
            intent = "facility_search"
            fac_info = tools.get_clinic_facilities_info(db)
            tool_executions.append({"tool_name": "get_clinic_facilities_info", "parameters": {}, "result": fac_info})
            reply = (
                "🏥 **How to Find Nearby Hospitals & Healthcare Facilities:**\n\n"
                "1. Click on **Facilities** in the top navigation bar.\n"
                "2. Filter by facility type (**Hospital**, **Specialized Clinic**, **Trauma Center**, or **Pathology Lab**) or by city.\n"
                "3. View facility address, 24/7 emergency hotlines, operating hours, and specialty departments.\n\n"
                "**ClinicCare Network Facilities:**\n\n"
            )
            for f in fac_info["facilities"][:3]:
                reply += f"• **{f['name']}** ({f['type'].replace('_', ' ').capitalize()} - {f['city']})\n"
                reply += f"  📍 {f['services']} | 📞 Hotline: {f['hotline']} | ⏰ {f['hours']}\n\n"
            suggested_actions = ["Healthcare Facilities", "Book Appointment", "Emergency 911/112"]

        # 15. How to Book an Appointment / Booking Guidance
        elif any(w in msg for w in ["how do i book an appointment", "how to book an appointment", "how to book", "book an appointment", "book appointment", "appointment booking", "appointment book", "appointment lena hai"]):
            intent = "book_appointment"
            reply = (
                "📅 **How to Book an Appointment in ClinicCare:**\n\n"
                "1. Navigate to **Book Appointment** from the navigation bar or patient dashboard.\n"
                "2. Select your required **Department** (e.g. Cardiology, Neurology, Orthopedics, Pediatrics).\n"
                "3. Choose your specialist **Doctor** and review qualifications and consultation fees.\n"
                "4. Pick your preferred **Consultation Date** and choose an open **Time Slot**.\n"
                "5. Enter the consultation reason and click **Confirm Appointment**.\n"
                "6. Your booking is confirmed instantly and tracked under **My Appointments**!"
            )
            suggested_actions = ["Book Appointment", "Check Doctors", "Check Slots"]

        # 16. Patient Search / Lookup
        elif any(w in msg for w in ["find patient", "search patient", "patient info", "patient lookup"]):
            intent = "patient_search"
            reply = "🔍 **Patient Record Lookup**: Admin and Front Desk staff can search patients by Name, Patient ID, Phone Number, or Blood Group in the **Patient Directory**."
            suggested_actions = ["Open Patient Directory", "View Appointments", "Talk to Front Desk"]

        # 17. Emergency Requests Overview
        elif any(w in msg for w in ["show emergency", "emergency requests", "emergency list"]):
            intent = "emergency_requests_overview"
            reply = (
                f"🚨 **Emergency & Triage Coordination**\n\n"
                f"Emergency hotline: **{settings.EMERGENCY_HOTLINE}**\n"
                "All urgent clinical cases and ambulance dispatches are triaged in real-time by the Front Desk and Emergency OPD teams."
            )
            suggested_actions = ["Emergency Dashboard", "Ambulance Fleet", "Call Emergency"]

        # Default Greeting / Helpful AI response
        else:
            intent = "greeting"
            reply = (
                f"Hello! 👋 Welcome to **{settings.HOSPITAL_NAME}** AI Patient Support.\n\n"
                "I can help you with:\n"
                "• 📅 Booking, rescheduling & cancelling appointments\n"
                "• 🚑 Requesting & tracking emergency ambulances\n"
                "• 🩸 Searching blood groups & requesting blood units\n"
                "• 🏥 Discovering nearby healthcare facilities & specialists\n"
                "• 💊 General educational drug information\n"
                "• 📄 Checking diagnostic lab report statuses\n\n"
                "How can I assist you today?"
            )

        return {
            "reply": reply,
            "intent": intent,
            "tool_calls": tool_executions,
            "suggested_actions": suggested_actions,
            "is_emergency": False,
        }


class GeminiAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._initialized = False
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name=self.model_name)
            self._initialized = True
        except Exception as e:
            print(f"Failed to initialize Gemini AI: {e}")
            self._initialized = False

    def generate_chat_response(
        self,
        db: Session,
        patient_id: Optional[str],
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self._initialized:
            fallback = RuleBasedFallbackProvider()
            return fallback.generate_chat_response(db, patient_id, user_message, conversation_history, conversation_id)

        try:
            from app.ai.prompts import HOSPITAL_AI_SYSTEM_PROMPT
            h_info = tools.get_hospital_doctor_info(db)
            context = f"{HOSPITAL_AI_SYSTEM_PROMPT}\n\nHOSPITAL DIRECTORY DATA:\n{json.dumps(h_info, indent=2)}\n\n"
            
            chat = self._model.start_chat(history=[])
            prompt = f"{context}\n\nPatient message: {user_message}\nProvide a helpful, accurate, concise reply strictly adhering to medical safety."
            response = chat.send_message(prompt)
            
            return {
                "reply": response.text,
                "intent": "gemini_response",
                "tool_calls": [],
                "suggested_actions": ["Book Appointment", "Check Doctors", "Report Status"],
                "is_emergency": False
            }
        except Exception as e:
            print(f"Gemini API error, falling back: {e}")
            fallback = RuleBasedFallbackProvider()
            return fallback.generate_chat_response(db, patient_id, user_message, conversation_history, conversation_id)


def get_ai_provider() -> BaseAIProvider:
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        return GeminiAIProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
    return RuleBasedFallbackProvider()
