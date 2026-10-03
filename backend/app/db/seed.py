import os
import sys
from datetime import date, datetime, timedelta, timezone

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from app.db.session import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models.clinic import Clinic
from app.models.audit import AuditLog
from app.models.user import User, Patient, Doctor, Department
from app.models.appointment import Appointment, DoctorSlot
from app.models.report import Report
from app.models.feedback import Feedback
from app.models.ai import AIConversation, AIMessage
from app.models.voice import VoiceCallRequest
from app.models.escalation import Escalation
from app.models.error_log import ErrorLog
from app.models.ambulance import Ambulance, AmbulanceRequest
from app.models.blood import BloodBank, BloodInventory
from app.models.facility import Facility
from app.models.visit import VisitHistory
from app.models.reminder import FollowUpReminder
from app.services.clinic_service import clinic_service
from app.services.audit_service import audit_service




def ensure_demo_accounts(db: SessionLocal):
    """Guarantees all 4 demo role logins exist and have valid credentials and active profiles."""
    from app.core.security import get_password_hash
    from app.models.user import User, Patient, Doctor, Department

    # 1. Admin
    admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.com")
    admin_pass = os.getenv("ADMIN_PASSWORD", "Admin@123")
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            password_hash=get_password_hash(admin_pass),
            full_name="Hospital Administrator",
            phone="+1 (800) 555-0100",
            role="ADMIN",
            is_active=True,
        )
        db.add(admin)
        db.flush()
    else:
        admin.password_hash = get_password_hash(admin_pass)
        admin.is_active = True
        admin.role = "ADMIN"

    # 2. Front Desk
    frontdesk = db.query(User).filter(User.email == "frontdesk@hospital.com").first()
    if not frontdesk:
        frontdesk = User(
            email="frontdesk@hospital.com",
            password_hash=get_password_hash("FrontDesk@123"),
            full_name="Front Desk Reception",
            phone="+1 (800) 555-0101",
            role="FRONT_DESK",
            is_active=True,
        )
        db.add(frontdesk)
        db.flush()
    else:
        frontdesk.password_hash = get_password_hash("FrontDesk@123")
        frontdesk.is_active = True
        frontdesk.role = "FRONT_DESK"

    # 3. Patient
    pat_user = db.query(User).filter(User.email == "patient@hospital.com").first()
    if not pat_user:
        pat_user = User(
            email="patient@hospital.com",
            password_hash=get_password_hash("Patient@123"),
            full_name="John Doe",
            phone="+1 (555) 123-4567",
            role="PATIENT",
            is_active=True,
        )
        db.add(pat_user)
        db.flush()
    else:
        pat_user.password_hash = get_password_hash("Patient@123")
        pat_user.is_active = True
        pat_user.role = "PATIENT"

    if not pat_user.patient_profile:
        pat_prof = Patient(
            user_id=pat_user.id,
            date_of_birth=date(1988, 5, 14),
            gender="male",
            blood_group="O+",
            address="123 Maple Street, Cityville",
            emergency_contact="Jane Doe - +1 (555) 987-6543",
        )
        db.add(pat_prof)
        db.flush()

    # 4. Doctors: dr.sharma@hospital.com & doctor@hospital.com
    first_dept = db.query(Department).first()
    if not first_dept:
        first_dept = Department(
            name="Cardiology",
            description="Specialized cardiovascular and heart care unit.",
            icon="Heart",
            is_active=True
        )
        db.add(first_dept)
        db.flush()

    for doc_email in ["dr.sharma@hospital.com", "doctor@hospital.com"]:
        doc_u = db.query(User).filter(User.email == doc_email).first()
        if not doc_u:
            doc_u = User(
                email=doc_email,
                password_hash=get_password_hash("Doctor@123"),
                full_name="Dr. Rajesh Sharma",
                phone="+1 (800) 555-0110",
                role="DOCTOR",
                is_active=True,
            )
            db.add(doc_u)
            db.flush()
        else:
            doc_u.password_hash = get_password_hash("Doctor@123")
            doc_u.is_active = True
            doc_u.role = "DOCTOR"

        if not doc_u.doctor_profile:
            doc_p = Doctor(
                user_id=doc_u.id,
                department_id=first_dept.id,
                specialization="Interventional Cardiologist",
                qualification="MD, DM (Cardiology), FACC",
                experience_years=15,
                consultation_fee=120.00,
                location="Block A, OPD 101",
                available_days="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
                available_hours_start="09:00",
                available_hours_end="17:00",
                slot_duration_minutes=30,
                is_active=True,
            )
            db.add(doc_p)
            db.flush()

    # 5. Super Admin
    super_admin = db.query(User).filter(User.email == "superadmin@hospital.com").first()
    if not super_admin:
        super_admin = User(
            email="superadmin@hospital.com",
            password_hash=get_password_hash("Super@123"),
            full_name="Enterprise Super Administrator",
            phone="+91 (800) 555-0190",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(super_admin)
        db.flush()
    else:
        super_admin.password_hash = get_password_hash("Super@123")
        super_admin.is_active = True
        super_admin.role = "SUPER_ADMIN"

    # 6. Organization Admin
    org_admin = db.query(User).filter(User.email == "orgadmin@hospital.com").first()
    if not org_admin:
        org_admin = User(
            email="orgadmin@hospital.com",
            password_hash=get_password_hash("Org@123"),
            full_name="Apollo Organization Administrator",
            phone="+91 (800) 555-0191",
            role="ORGANIZATION_ADMIN",
            is_active=True,
        )
        db.add(org_admin)
        db.flush()
    else:
        org_admin.password_hash = get_password_hash("Org@123")
        org_admin.is_active = True
        org_admin.role = "ORGANIZATION_ADMIN"

    # Ensure Organization and Branches
    try:
        from app.models.organization import Organization, Branch
        org = db.query(Organization).filter(Organization.code == "APOLLO").first()
        if not org:
            org = Organization(
                name="Apollo Care Healthcare Network",
                code="APOLLO",
                email="hq@apollocare.com",
                phone="+91 (800) 555-0199",
                headquarters_address="Apollo Central Towers, MG Road, Bengaluru",
                is_active=True,
            )
            db.add(org)
            db.flush()

        primary_clinic = db.query(Clinic).first()
        if primary_clinic and not primary_clinic.organization_id:
            primary_clinic.organization_id = org.id
            db.flush()

        branch = db.query(Branch).filter(Branch.organization_id == org.id).first()
        if not branch:
            branch = Branch(
                organization_id=org.id,
                clinic_id=primary_clinic.id if primary_clinic else None,
                name="Apollo Central Hospital Branch",
                code="CENTRAL-01",
                address="123 Healthcare Avenue",
                city="Bengaluru",
                state="Karnataka",
                pincode="560001",
                phone="+91 80 2345 6789",
                email="central@apollocare.com",
                operating_hours="24/7 Emergency & OPD (08:00 AM - 09:00 PM)",
                is_active=True,
            )
            db.add(branch)
            db.flush()

        if org_admin:
            org_admin.organization_id = org.id
            org_admin.branch_id = branch.id
            if primary_clinic:
                org_admin.clinic_id = primary_clinic.id
    except Exception as e:
        print(f"[Seed] Warning ensuring organization/branch: {e}")

    db.commit()


def ensure_tenant_columns(db_engine):
    """Ensures multi-tenant columns exist on legacy database tables safely."""
    try:
        with db_engine.connect() as conn:
            dialect = db_engine.dialect.name
            target_cols = [
                ("users", "clinic_id", "VARCHAR(36)"),
                ("departments", "clinic_id", "VARCHAR(36)"),
                ("appointments", "clinic_id", "VARCHAR(36)"),
                ("reports", "clinic_id", "VARCHAR(36)"),
                ("appointments", "appointment_type", "VARCHAR(50) DEFAULT 'NEW_CONSULTATION'"),
                ("appointments", "token_number", "VARCHAR(20)"),
                ("appointments", "queue_status", "VARCHAR(30) DEFAULT 'NOT_QUEUED'"),
                ("appointments", "checked_in_at", "DATETIME"),
                ("appointments", "consultation_started_at", "DATETIME"),
                ("appointments", "consultation_ended_at", "DATETIME"),
                ("appointments", "is_walk_in", "BOOLEAN DEFAULT 0"),
                ("appointments", "parent_appointment_id", "VARCHAR(36)"),
                ("doctors", "break_start_time", "VARCHAR(10) DEFAULT '13:00'"),
                ("doctors", "break_end_time", "VARCHAR(10) DEFAULT '14:00'"),
                ("doctors", "max_daily_patients", "INTEGER DEFAULT 30"),
            ]
            if dialect == "sqlite":
                for tbl, col, col_type in target_cols:
                    try:
                        res = conn.execute(text(f"PRAGMA table_info({tbl})")).fetchall()
                        cols = [r[1] for r in res]
                        if cols and col not in cols:
                            conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type}"))
                            conn.commit()
                    except Exception as err:
                        print(f"[Seed Migration Notice] {tbl}.{col}: {err}")
            elif dialect == "postgresql":
                for tbl, col, col_type in target_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                        conn.commit()
                    except Exception as err:
                        print(f"[Seed PG Migration Notice] {tbl}.{col}: {err}")
    except Exception as e:
        print(f"[Seed] Column check warning: {e}")


def seed_database():
    print("Initializing database tables...")
    ensure_tenant_columns(engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Guarantee default central tenant exists
        default_clinic = clinic_service.get_or_create_default_clinic(db)

        # Guarantee demo accounts exist and are functional
        ensure_demo_accounts(db)

        # Associate existing entities without clinic_id with default tenant
        db.query(User).filter(User.clinic_id == None).update({User.clinic_id: default_clinic.id}, synchronize_session=False)
        db.query(Department).filter(Department.clinic_id == None).update({Department.clinic_id: default_clinic.id}, synchronize_session=False)
        db.query(Appointment).filter(Appointment.clinic_id == None).update({Appointment.clinic_id: default_clinic.id}, synchronize_session=False)
        db.query(Report).filter(Report.clinic_id == None).update({Report.clinic_id: default_clinic.id}, synchronize_session=False)
        db.commit()

        # Seed initial system audit entry if empty
        if not db.query(AuditLog).first():
            admin_u = db.query(User).filter(User.email == "admin@hospital.com").first()
            audit_service.log_action(
                db=db,
                action="SYSTEM_INIT",
                user=admin_u,
                clinic_id=default_clinic.id,
                entity_type="Clinic",
                entity_id=default_clinic.id,
                details={"message": "ClinicCare SaaS Foundation Phase 1 Initialized", "default_clinic": default_clinic.name}
            )

        # Check if already seeded
        admin_check = db.query(User).filter(User.email == "admin@hospital.com").first()
        if admin_check:
            from app.models.ambulance import Ambulance
            if not db.query(Ambulance).first():
                print("Extending existing database with FIT-FEST 2026 data...")
                primary_patient = db.query(Patient).first()
                primary_doctor = db.query(Doctor).first()
                primary_app = db.query(Appointment).first()
                today = date.today()
                
                # Seed Ambulances
                amb1 = Ambulance(vehicle_number="AMB-101-BLS", model="Mercedes Sprinter BLS", ambulance_type="Basic Life Support (BLS)", status="available", base_station="ClinicCare Main Campus", current_location="Main Base, Bay 1", driver_name="Robert Jenkins", driver_phone="+1 (800) 555-0301", is_active=True)
                amb2 = Ambulance(vehicle_number="AMB-102-ALS", model="Ford Transit Mobile ICU", ambulance_type="Advanced Cardiac Life Support (ALS)", status="available", base_station="ClinicCare North Satellite", current_location="North Hub, Station 2", driver_name="Michael Vance", driver_phone="+1 (800) 555-0302", is_active=True)
                amb3 = Ambulance(vehicle_number="AMB-103-CCU", model="Freightliner Critical Care", ambulance_type="Critical Care Transport", status="busy", base_station="ClinicCare Main Campus", current_location="En route to 742 Evergreen Terrace", driver_name="David Rodriguez", driver_phone="+1 (800) 555-0303", is_active=True)
                db.add_all([amb1, amb2, amb3])
                db.flush()

                if primary_patient:
                    amb_req1 = AmbulanceRequest(patient_id=primary_patient.id, ambulance_id=amb3.id, requester_name=primary_patient.user.full_name, requester_phone=primary_patient.user.phone or "+15550001", pickup_address="742 Evergreen Terrace, Springfield", destination_facility="ClinicCare Multispeciality Hospital", emergency_priority="critical", status="en_route", notes="Patient experiencing acute chest tightness.", is_simulated=True)
                    db.add(amb_req1)

                # Seed Blood Banks
                bb1 = BloodBank(name="ClinicCare Central Blood Bank", city="Metropolis", address="Building C, ClinicCare Complex", phone="+1 (800) 555-0400", email="bloodbank@hospital.com", is_verified=True)
                bb2 = BloodBank(name="Red Cross Regional Blood Center", city="Metropolis", address="108 Health Blvd", phone="+1 (800) 555-0401", email="transfusion@redcross.org", is_verified=True)
                db.add_all([bb1, bb2])
                db.flush()

                for bg, units, stat in [("A+", 18, "available"), ("A-", 6, "available"), ("B+", 22, "available"), ("B-", 4, "low_stock"), ("AB+", 12, "available"), ("AB-", 2, "low_stock"), ("O+", 30, "available"), ("O-", 3, "critical_need")]:
                    db.add_all([BloodInventory(blood_bank_id=bb1.id, blood_group=bg, units_available=units, status=stat), BloodInventory(blood_bank_id=bb2.id, blood_group=bg, units_available=max(1, units - 2), status=stat)])

                # Facilities
                fac1 = Facility(name="ClinicCare Multispeciality Hospital (Main Campus)", facility_type="Multispeciality Hospital & Trauma Center", services="Cardiology, Neurology, Pediatrics, Orthopedics, General Medicine, 24/7 ICU, Emergency Trauma", address="100 Hospital Drive, Healthcare City, Metropolis", city="Metropolis", phone="+1 (800) 555-0100", emergency_hotline="911 / +1 (800) 555-0199", is_emergency_ready=True, rating=4.9, is_active=True)
                fac2 = Facility(name="ClinicCare Westside Family Care Clinic", facility_type="Outpatient Primary Care Clinic", services="General Medicine, Routine Vaccinations, Pediatric Consultations", address="45 West Market Avenue, Suite 200, Metropolis", city="Metropolis", phone="+1 (800) 555-0150", emergency_hotline="+1 (800) 555-0199", is_emergency_ready=False, rating=4.7, is_active=True)
                fac3 = Facility(name="ClinicCare Advanced Diagnostic & Imaging Center", facility_type="Diagnostic & Pathology Laboratory", services="MRI, CT Scan, Ultrasound, Automated Biochemistry, Digital X-Ray", address="102 Hospital Drive, Annex B, Metropolis", city="Metropolis", phone="+1 (800) 555-0160", emergency_hotline="+1 (800) 555-0199", is_emergency_ready=True, rating=4.8, is_active=True)
                db.add_all([fac1, fac2, fac3])

                if primary_patient and primary_doctor:
                    vh1 = VisitHistory(patient_id=primary_patient.id, doctor_id=primary_doctor.id, department_id=primary_doctor.department_id, appointment_id=primary_app.id if primary_app else None, visit_date=today - timedelta(days=1), visit_type="OPD Consultation", visit_status="completed", vitals_summary="BP: 124/82 mmHg | Pulse: 74 bpm | SpO2: 99%", administrative_notes="Consultation fees settled.", follow_up_instructions="Routine follow-up in 4 weeks.")
                    db.add(vh1)
                    rem1 = FollowUpReminder(patient_id=primary_patient.id, appointment_id=primary_app.id if primary_app else None, doctor_id=primary_doctor.id, reminder_type="upcoming_appointment", scheduled_for=datetime.combine(today + timedelta(days=1), datetime.min.time()), title="Cardiology Consultation Follow-up", message="Automated reminder for your appointment tomorrow.", channel="WhatsApp/SMS (Demo)", status="scheduled")
                    db.add(rem1)

                db.commit()
                print("FIT-FEST 2026 data populated successfully!")
                return
            else:
                print("Database is already seeded with demo data.")
                return


        print("Seeding Departments...")
        depts_data = [
            ("Cardiology", "Specialized cardiovascular and heart care unit offering advanced diagnostics and interventions.", "Heart"),
            ("Neurology", "Comprehensive diagnosis and therapy for brain, spine, and nervous system disorders.", "Brain"),
            ("Pediatrics", "Dedicated pediatric health services and care from newborn through adolescence.", "Baby"),
            ("Orthopedics", "Expert joint replacement, fracture care, and musculoskeletal rehabilitation.", "Bone"),
            ("General Medicine", "Primary healthcare, preventive medicine, chronic disease management, and triage.", "Stethoscope"),
        ]
        dept_map = {}
        for name, desc, icon in depts_data:
            dept = Department(name=name, description=desc, icon=icon, is_active=True)
            db.add(dept)
            db.flush()
            dept_map[name] = dept.id

        print("Seeding Admin and Front Desk Staff...")
        admin = User(
            email="admin@hospital.com",
            password_hash=get_password_hash("Admin@123"),
            full_name="Hospital Administrator",
            phone="+1 (800) 555-0100",
            role="ADMIN",
            is_active=True,
        )
        db.add(admin)

        frontdesk = User(
            email="frontdesk@hospital.com",
            password_hash=get_password_hash("FrontDesk@123"),
            full_name="Front Desk Reception",
            phone="+1 (800) 555-0101",
            role="FRONT_DESK",
            is_active=True,
        )
        db.add(frontdesk)
        db.flush()

        print("Seeding Doctors...")
        doctors_info = [
            ("doctor@hospital.com", "Dr. Rajesh Sharma", "Cardiology", "Chief Medical Officer & Cardiologist", "MD, DM, FACC", 18, 120.00, "Block A, OPD 100", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"),
            ("dr.sharma@hospital.com", "Dr. Rajesh Sharma", "Cardiology", "Interventional Cardiologist", "MD, DM (Cardiology), FACC", 15, 120.00, "Block A, OPD 101", "Monday,Tuesday,Wednesday,Thursday,Friday"),
            ("dr.patel@hospital.com", "Dr. Ananya Patel", "Cardiology", "Electrophysiologist & Heart Care", "MBBS, MD, FESC", 11, 110.00, "Block A, OPD 102", "Monday,Wednesday,Friday,Saturday"),
            ("dr.chen@hospital.com", "Dr. Marcus Chen", "Neurology", "Senior Neurosurgeon", "MD, MCh (Neurosurgery)", 18, 150.00, "Block B, OPD 201", "Monday,Tuesday,Thursday,Friday"),
            ("dr.kumar@hospital.com", "Dr. Priya Kumar", "Neurology", "Clinical Neurologist & Epilepsy Specialist", "MBBS, MD, DM", 9, 100.00, "Block B, OPD 202", "Tuesday,Wednesday,Friday,Saturday"),
            ("dr.adams@hospital.com", "Dr. Sarah Adams", "Pediatrics", "Consultant Pediatrician", "MD (Pediatrics), FAAP", 12, 90.00, "Block C, OPD 301", "Monday,Tuesday,Wednesday,Thursday,Friday"),
            ("dr.gupta@hospital.com", "Dr. Rohan Gupta", "Pediatrics", "Neonatologist & Child Specialist", "MBBS, DCH, DNB", 8, 85.00, "Block C, OPD 302", "Monday,Wednesday,Thursday,Saturday"),
            ("dr.miller@hospital.com", "Dr. David Miller", "Orthopedics", "Joint Replacement Surgeon", "MS (Ortho), MCh (Ortho)", 16, 130.00, "Block D, OPD 401", "Monday,Tuesday,Wednesday,Friday"),
            ("dr.singh@hospital.com", "Dr. Harpreet Singh", "Orthopedics", "Sports Injury & Spine Specialist", "MBBS, MS (Ortho)", 10, 105.00, "Block D, OPD 402", "Tuesday,Thursday,Saturday"),
            ("dr.taylor@hospital.com", "Dr. Emily Taylor", "General Medicine", "Internal Medicine Physician", "MD (Internal Medicine)", 14, 80.00, "Main Clinic, OPD 01", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"),
            ("dr.rao@hospital.com", "Dr. Suresh Rao", "General Medicine", "Family Physician & Diabetologist", "MBBS, MD", 19, 75.00, "Main Clinic, OPD 02", "Monday,Tuesday,Wednesday,Thursday,Friday"),
        ]

        doc_entities = []
        for email, name, dept_name, spec, qual, exp, fee, loc, days in doctors_info:
            user = User(
                email=email,
                password_hash=get_password_hash("Doctor@123"),
                full_name=name,
                phone=f"+1 (800) 555-0{len(doc_entities) + 110}",
                role="DOCTOR",
                is_active=True,
            )
            db.add(user)
            db.flush()

            doc = Doctor(
                user_id=user.id,
                department_id=dept_map[dept_name],
                specialization=spec,
                qualification=qual,
                experience_years=exp,
                consultation_fee=fee,
                location=loc,
                available_days=days,
                available_hours_start="09:00",
                available_hours_end="17:00",
                slot_duration_minutes=30,
                is_active=True,
            )
            db.add(doc)
            db.flush()
            doc_entities.append(doc)

        print("Seeding Patients...")
        patient_names = [
            ("patient@hospital.com", "John Doe", "+1 (555) 123-4567", "1988-05-14", "male", "O+", "123 Maple Street, Cityville", "Jane Doe - +1 (555) 987-6543"),
            ("alice.smith@example.com", "Alice Smith", "+1 (555) 234-5678", "1992-08-22", "female", "A+", "456 Oak Avenue, Cityville", "Bob Smith - +1 (555) 876-5432"),
            ("rahul.verma@example.com", "Rahul Verma", "+1 (555) 345-6789", "1985-11-03", "male", "B+", "789 Pine Road, Cityville", "Pooja Verma - +1 (555) 765-4321"),
            ("maria.garcia@example.com", "Maria Garcia", "+1 (555) 456-7890", "1995-02-18", "female", "AB+", "101 Cedar Lane, Cityville", "Carlos Garcia - +1 (555) 654-3210"),
            ("david.kim@example.com", "David Kim", "+1 (555) 567-8901", "1979-07-30", "male", "O-", "202 Elm Street, Cityville", "Grace Kim - +1 (555) 543-2109"),
            ("priya.nair@example.com", "Priya Nair", "+1 (555) 678-9012", "1990-12-05", "female", "A-", "303 Birch Court, Cityville", "Karthik Nair - +1 (555) 432-1098"),
            ("michael.brown@example.com", "Michael Brown", "+1 (555) 789-0123", "1983-04-25", "male", "B-", "404 Walnut Drive, Cityville", "Sarah Brown - +1 (555) 321-0987"),
            ("fatima.khan@example.com", "Fatima Khan", "+1 (555) 890-1234", "1997-09-12", "female", "O+", "505 Ash Street, Cityville", "Tariq Khan - +1 (555) 210-9876"),
            ("james.wilson@example.com", "James Wilson", "+1 (555) 901-2345", "1975-01-19", "male", "AB-", "606 Spruce Boulevard, Cityville", "Linda Wilson - +1 (555) 109-8765"),
            ("anita.desai@example.com", "Anita Desai", "+1 (555) 012-3456", "1989-06-11", "female", "O+", "707 Willow Way, Cityville", "Ravi Desai - +1 (555) 098-7654"),
        ]

        patients_list = []
        for email, name, phone, dob, gender, blood, addr, em_contact in patient_names:
            u = User(
                email=email,
                password_hash=get_password_hash("Patient@123"),
                full_name=name,
                phone=phone,
                role="PATIENT",
                is_active=True,
            )
            db.add(u)
            db.flush()

            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            pat = Patient(
                user_id=u.id,
                date_of_birth=dob_date,
                gender=gender,
                blood_group=blood,
                address=addr,
                emergency_contact=em_contact,
            )
            db.add(pat)
            db.flush()
            patients_list.append(pat)

        primary_patient = patients_list[0]

        print("Seeding Doctor Slots & Appointments...")
        today = date.today()
        # Create slots for upcoming 7 days
        for doc in doc_entities:
            for day_offset in range(7):
                s_date = today + timedelta(days=day_offset)
                for h in [9, 10, 11, 14, 15, 16]:
                    slot = DoctorSlot(
                        doctor_id=doc.id,
                        slot_date=s_date,
                        start_time=f"{h:02d}:00",
                        end_time=f"{h:02d}:30",
                        is_booked=False,
                    )
                    db.add(slot)

        db.flush()

        # Seed realistic appointments
        app1 = Appointment(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[0].id,
            department_id=doc_entities[0].department_id,
            appointment_date=today + timedelta(days=1),
            appointment_time="10:00",
            status="confirmed",
            reason="Routine cardiac health checkup and BP review.",
            notes="Patient has mild hypertension history.",
        )
        db.add(app1)

        app2 = Appointment(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[8].id,
            department_id=doc_entities[8].department_id,
            appointment_date=today - timedelta(days=10),
            appointment_time="11:00",
            status="completed",
            reason="Seasonal flu symptoms and persistent cough.",
            notes="Prescribed rest and recovery plan.",
        )
        db.add(app2)

        app3 = Appointment(
            patient_id=patients_list[1].id,
            doctor_id=doc_entities[2].id,
            department_id=doc_entities[2].department_id,
            appointment_date=today + timedelta(days=2),
            appointment_time="14:00",
            status="confirmed",
            reason="Frequent migraine headaches and light sensitivity.",
        )
        db.add(app3)

        app4 = Appointment(
            patient_id=patients_list[2].id,
            doctor_id=doc_entities[6].id,
            department_id=doc_entities[6].department_id,
            appointment_date=today + timedelta(days=3),
            appointment_time="09:00",
            status="confirmed",
            reason="Knee pain after sports activity.",
        )
        db.add(app4)

        print("Seeding Diagnostic Reports...")
        rep1 = Report(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[0].id,
            title="Comprehensive Lipid Profile & Blood Panel",
            report_type="Blood Test",
            status="ready",
            file_url="https://example.com/reports/lipid_profile_001.pdf",
            notes="Cholesterol levels within normal range. HDL is optimal.",
            report_date=today - timedelta(days=5),
        )
        rep2 = Report(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[0].id,
            title="12-Lead Electrocardiogram (ECG)",
            report_type="ECG",
            status="ready",
            file_url="https://example.com/reports/ecg_001.pdf",
            notes="Normal sinus rhythm. No acute ST-T changes observed.",
            report_date=today - timedelta(days=7),
        )
        rep3 = Report(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[8].id,
            title="HbA1c & Fasting Blood Sugar",
            report_type="Pathology",
            status="processing",
            notes="Sample in laboratory processing queue.",
            report_date=today,
        )
        rep4 = Report(
            patient_id=patients_list[1].id,
            doctor_id=doc_entities[2].id,
            title="Brain MRI Scan with Contrast",
            report_type="MRI",
            status="delivered",
            file_url="https://example.com/reports/mri_brain_002.pdf",
            notes="Delivered to patient and consulting neurologist.",
            report_date=today - timedelta(days=12),
        )
        db.add_all([rep1, rep2, rep3, rep4])
        db.flush()

        print("Seeding Feedback...")
        fb1 = Feedback(
            patient_id=primary_patient.id,
            appointment_id=app2.id,
            rating=5,
            comment="Dr. Emily Taylor was very compassionate, clear in explanation, and attentive.",
            status="active",
        )
        db.add(fb1)

        print("Seeding AI Conversations...")
        conv1 = AIConversation(
            patient_id=primary_patient.id,
            channel="web",
            title="Inquiry about Cardiology Consultation",
            is_active=True,
        )
        db.add(conv1)
        db.flush()

        m1 = AIMessage(
            conversation_id=conv1.id,
            sender="patient",
            content="Hello, what are the consultation hours for Dr. Sharma in Cardiology?",
        )
        m2 = AIMessage(
            conversation_id=conv1.id,
            sender="ai",
            content="Hello John! Dr. Rajesh Sharma is available Monday to Friday from 09:00 to 17:00 at Block A, OPD 101. The consultation fee is $120.00. Would you like to check available appointment slots?",
            intent="hospital_info",
        )
        db.add_all([m1, m2])

        print("Seeding Escalations & Voice Calls...")
        esc1 = Escalation(
            patient_id=patients_list[3].id,
            reason="billing",
            status="open",
            priority="medium",
            resolution_notes="Patient has inquiry regarding insurance coverage clearance.",
        )
        db.add(esc1)

        vc1 = VoiceCallRequest(
            patient_id=primary_patient.id,
            phone=primary_patient.user.phone,
            reason="Patient requested AI voice callback for appointment reminder confirmation.",
            status="completed",
            requested_at=datetime.now(timezone.utc) - timedelta(hours=2),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=1),
            notes="Voice call successfully completed.",
        )
        db.add(vc1)

        print("Seeding Error Logs...")
        err1 = ErrorLog(
            service_name="whatsapp-webhook",
            error_level="INFO",
            message="WhatsApp webhook ping received with verification challenge",
            endpoint="/api/whatsapp/webhook",
        )
        db.add(err1)

        # Seed FIT-FEST 2026 Additions
        print("Seeding Ambulances & Ambulance Requests...")
        amb1 = Ambulance(
            vehicle_number="AMB-101-BLS",
            model="Mercedes-Benz Sprinter BLS",
            ambulance_type="Basic Life Support (BLS)",
            status="available",
            base_station="ClinicCare Main Campus",
            current_location="Main Campus, Emergency Bay 1",
            driver_name="Robert Jenkins",
            driver_phone="+1 (800) 555-0301",
            paramedic_name="Nurse Sarah Connor",
            is_active=True,
        )
        amb2 = Ambulance(
            vehicle_number="AMB-102-ALS",
            model="Ford Transit Mobile ICU",
            ambulance_type="Advanced Cardiac Life Support (ALS)",
            status="available",
            base_station="ClinicCare North Satellite",
            current_location="North Hub, Station 2",
            driver_name="Michael Vance",
            driver_phone="+1 (800) 555-0302",
            paramedic_name="Paramedic Alex Turner",
            is_active=True,
        )
        amb3 = Ambulance(
            vehicle_number="AMB-103-CCU",
            model="Freightliner Critical Care Mobile",
            ambulance_type="Critical Care Transport",
            status="busy",
            base_station="ClinicCare Main Campus",
            current_location="En route to 742 Evergreen Terrace",
            driver_name="David Rodriguez",
            driver_phone="+1 (800) 555-0303",
            paramedic_name="Paramedic Elena Rostova",
            is_active=True,
        )
        db.add_all([amb1, amb2, amb3])
        db.flush()

        amb_req1 = AmbulanceRequest(
            patient_id=primary_patient.id,
            ambulance_id=amb3.id,
            requester_name=primary_patient.user.full_name,
            requester_phone=primary_patient.user.phone,
            pickup_address="742 Evergreen Terrace, Springfield",
            destination_facility="ClinicCare Multispeciality Hospital",
            emergency_priority="critical",
            status="en_route",
            notes="Patient experiencing acute chest tightness. ALS unit dispatched.",
            is_simulated=True,
        )
        db.add(amb_req1)

        print("Seeding Blood Banks & Inventory...")
        bb1 = BloodBank(
            name="ClinicCare Central Blood Bank & Component Lab",
            city="Metropolis",
            address="Building C, Ground Floor, ClinicCare Medical Complex",
            phone="+1 (800) 555-0400",
            email="bloodbank@cliniccarehospital.com",
            operating_hours="24/7 Continuous Emergency Service",
            is_verified=True,
        )
        bb2 = BloodBank(
            name="Red Cross Regional Blood Transfusion Center",
            city="Metropolis",
            address="108 Health Boulevard, Central District",
            phone="+1 (800) 555-0401",
            email="transfusion@redcross-metro.org",
            operating_hours="24/7 Emergency Transfusion Ready",
            is_verified=True,
        )
        db.add_all([bb1, bb2])
        db.flush()

        blood_groups_data = [
            ("A+", 18, "available"),
            ("A-", 6, "available"),
            ("B+", 22, "available"),
            ("B-", 4, "low_stock"),
            ("AB+", 12, "available"),
            ("AB-", 2, "low_stock"),
            ("O+", 30, "available"),
            ("O-", 3, "critical_need"),
        ]
        for bg, units, stat in blood_groups_data:
            inv1 = BloodInventory(blood_bank_id=bb1.id, blood_group=bg, units_available=units, status=stat)
            inv2 = BloodInventory(blood_bank_id=bb2.id, blood_group=bg, units_available=max(1, units - 2), status=stat)
            db.add_all([inv1, inv2])

        print("Seeding Blood Requests...")
        br1 = BloodRequest(
            patient_id=primary_patient.id,
            patient_name=primary_patient.user.full_name,
            blood_group="O+",
            units_required=2,
            hospital_clinic_name="ClinicCare Multispeciality Hospital",
            location="Metropolis ICU Ward 3",
            contact_phone=primary_patient.user.phone or "+1 (800) 555-0100",
            urgency="urgent",
            additional_info="Patient scheduled for elective vascular procedure.",
            status="match_found",
            matched_blood_bank_id=bb1.id,
            matched_bank_name=f"{bb1.name} (Metropolis)",
            admin_notes="2 units allocated from Central Bank reserve.",
            is_simulated=True,
        )
        br2 = BloodRequest(
            patient_name="Sarah Jenkins",
            blood_group="AB-",
            units_required=1,
            hospital_clinic_name="Metropolis Community Clinic",
            location="Downtown West",
            contact_phone="+1 (800) 555-0211",
            urgency="critical",
            additional_info="Emergency surgery requirement.",
            status="searching",
            admin_notes="Searching regional component centers.",
            is_simulated=True,
        )
        db.add_all([br1, br2])

        print("Seeding Healthcare Facilities...")
        fac1 = Facility(
            name="ClinicCare Multispeciality Hospital (Main Campus)",
            facility_type="Multispeciality Hospital & Trauma Center",
            services="Cardiology, Neurology, Pediatrics, Orthopedics, General Medicine, 24/7 ICU, Emergency Trauma",
            address="100 Hospital Drive, Healthcare City, Metropolis",
            city="Metropolis",
            phone="+1 (800) 555-0100",
            emergency_hotline="911 / +1 (800) 555-0199",
            operating_hours="24/7 Emergency & Inpatient Care",
            is_emergency_ready=True,
            rating=4.9,
            is_active=True,
        )
        fac2 = Facility(
            name="ClinicCare Westside Family Care Clinic",
            facility_type="Outpatient Primary Care Clinic",
            services="General Medicine, Routine Vaccinations, Diagnostic Phlebotomy, Pediatric Consultations",
            address="45 West Market Avenue, Suite 200, Metropolis",
            city="Metropolis",
            phone="+1 (800) 555-0150",
            emergency_hotline="+1 (800) 555-0199",
            operating_hours="Monday - Saturday: 08:00 AM - 08:00 PM",
            is_emergency_ready=False,
            rating=4.7,
            is_active=True,
        )
        fac3 = Facility(
            name="ClinicCare Advanced Diagnostic & Imaging Center",
            facility_type="Diagnostic & Pathology Laboratory",
            services="MRI, CT Scan, Ultrasound, Automated Biochemistry, Digital X-Ray, Blood Bank Access",
            address="102 Hospital Drive, Annex B, Metropolis",
            city="Metropolis",
            phone="+1 (800) 555-0160",
            emergency_hotline="+1 (800) 555-0199",
            operating_hours="Monday - Sunday: 07:00 AM - 10:00 PM",
            is_emergency_ready=True,
            rating=4.8,
            is_active=True,
        )
        db.add_all([fac1, fac2, fac3])

        print("Seeding Visit History & Follow-Up Reminders...")
        vh1 = VisitHistory(
            patient_id=primary_patient.id,
            doctor_id=doc_entities[0].id,
            department_id=dept_map["Cardiology"],
            appointment_id=app1.id,
            visit_date=today - timedelta(days=1),
            visit_type="OPD Consultation",
            visit_status="completed",
            vitals_summary="BP: 124/82 mmHg | Pulse: 74 bpm | SpO2: 99% | Temp: 98.6°F",
            administrative_notes="Registration and consultation fees settled. ECG report attached to chart.",
            follow_up_instructions="Routine follow-up in 4 weeks. Continue healthy lifestyle and low-sodium diet.",
        )
        db.add(vh1)

        rem1 = FollowUpReminder(
            patient_id=primary_patient.id,
            appointment_id=app1.id,
            doctor_id=doc_entities[0].id,
            reminder_type="upcoming_appointment",
            scheduled_for=datetime.combine(today + timedelta(days=1), datetime.min.time()),
            title="Cardiology Consultation Follow-up",
            message="Hello John, this is an automated reminder for your follow-up consultation with Dr. Rajesh Sharma tomorrow at 10:00 AM.",
            channel="WhatsApp/SMS (Demo)",
            status="scheduled",
        )
        db.add(rem1)



        db.commit()
        print("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

