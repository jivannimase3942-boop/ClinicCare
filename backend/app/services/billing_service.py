from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.billing import Invoice, InvoiceItem, Payment, Refund
from app.models.clinic import Clinic
from app.models.user import Patient, Doctor, User
from app.schemas.billing import InvoiceCreate, PaymentCreate, RefundCreate, InvoiceResponse, InvoiceItemResponse, PaymentResponse, RefundResponse, RevenueSummaryResponse
from app.services.audit_service import audit_service


class BillingService:
    @staticmethod
    def _format_invoice(inv: Invoice) -> InvoiceResponse:
        clinic_name = inv.clinic.name if inv.clinic else None
        clinic_phone = inv.clinic.phone if inv.clinic else None
        clinic_address = inv.clinic.address if inv.clinic else None
        pat_name = inv.patient.user.full_name if inv.patient and inv.patient.user else None
        pat_phone = inv.patient.user.phone if inv.patient and inv.patient.user else None
        doc_name = inv.doctor.user.full_name if inv.doctor and inv.doctor.user else None

        items = [
            InvoiceItemResponse(
                id=item.id,
                item_type=item.item_type,
                description=item.description,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                total_price=float(item.total_price),
            )
            for item in inv.items
        ]

        payments = [
            PaymentResponse(
                id=p.id,
                invoice_id=p.invoice_id,
                amount=float(p.amount),
                payment_method=p.payment_method,
                transaction_reference=p.transaction_reference,
                notes=p.notes,
                created_at=p.created_at,
            )
            for p in inv.payments
        ]

        refunds = [
            RefundResponse(
                id=r.id,
                invoice_id=r.invoice_id,
                amount=float(r.amount),
                reason=r.reason,
                status=r.status,
                created_at=r.created_at,
            )
            for r in inv.refunds
        ]

        return InvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            clinic_id=inv.clinic_id,
            clinic_name=clinic_name,
            clinic_phone=clinic_phone,
            clinic_address=clinic_address,
            patient_id=inv.patient_id,
            patient_name=pat_name,
            patient_phone=pat_phone,
            appointment_id=inv.appointment_id,
            doctor_id=inv.doctor_id,
            doctor_name=doc_name,
            subtotal=float(inv.subtotal),
            discount_amount=float(inv.discount_amount),
            tax_rate_percent=float(inv.tax_rate_percent),
            tax_amount=float(inv.tax_amount),
            total_amount=float(inv.total_amount),
            amount_paid=float(inv.amount_paid),
            balance_due=float(inv.balance_due),
            status=inv.status,
            payment_method=inv.payment_method,
            notes=inv.notes,
            items=items,
            payments=payments,
            refunds=refunds,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        )

    @staticmethod
    def generate_invoice_number(db: Session, clinic_id: str) -> str:
        prefix = f"INV-{datetime.now().strftime('%Y%m')}"
        count = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}-%")
        ).count()
        cand = f"{prefix}-{(count + 1):04d}"
        existing = db.query(Invoice).filter(Invoice.invoice_number == cand).first()
        if existing:
            import uuid
            cand = f"{prefix}-{(count + 1):04d}-{uuid.uuid4().hex[:4].upper()}"
        return cand

    @staticmethod
    def create_invoice(
        db: Session,
        clinic_id: str,
        data: InvoiceCreate,
        actor_id: Optional[str] = None,
    ) -> InvoiceResponse:
        pat = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not pat:
            raise ValueError("Patient not found")

        # 1. Calculate line items
        subtotal = Decimal("0.00")
        db_items = []
        for it in data.items:
            qty = max(1, it.quantity)
            u_price = Decimal(str(round(it.unit_price, 2)))
            line_total = u_price * Decimal(qty)
            subtotal += line_total
            db_items.append(
                InvoiceItem(
                    item_type=it.item_type,
                    description=it.description,
                    quantity=qty,
                    unit_price=u_price,
                    total_price=line_total,
                )
            )

        # 2. Taxes and Discounts
        discount = Decimal(str(round(data.discount_amount, 2)))
        tax_pct = Decimal(str(round(data.tax_rate_percent, 2)))
        taxable = max(Decimal("0.00"), subtotal - discount)
        tax_amount = Decimal(str(round(float(taxable * (tax_pct / Decimal("100.0"))), 2)))
        total_amount = taxable + tax_amount

        inv_num = BillingService.generate_invoice_number(db, clinic_id)
        invoice = Invoice(
            invoice_number=inv_num,
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            doctor_id=data.doctor_id,
            subtotal=subtotal,
            discount_amount=discount,
            tax_rate_percent=tax_pct,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            balance_due=total_amount,
            status="PAID" if total_amount == 0 else "PENDING",
            notes=data.notes,
        )
        invoice.items = db_items
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="INVOICE_CREATE",
            entity_type="Invoice",
            entity_id=invoice.id,
            details={
                "invoice_number": inv_num,
                "patient_id": data.patient_id,
                "total_amount": float(total_amount),
            }
        )
        return BillingService._format_invoice(invoice)

    @staticmethod
    def record_payment(
        db: Session,
        invoice_id: str,
        data: PaymentCreate,
        clinic_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> InvoiceResponse:
        query = db.query(Invoice).filter(Invoice.id == invoice_id)
        if clinic_id:
            query = query.filter(Invoice.clinic_id == clinic_id)
        inv = query.first()
        if not inv:
            raise ValueError("Invoice not found or unauthorized")

        pay_amount = Decimal(str(round(data.amount, 2)))
        if pay_amount <= Decimal("0.00"):
            raise ValueError("Payment amount must be greater than zero")

        if pay_amount > inv.balance_due:
            raise ValueError(f"Payment amount ({pay_amount}) cannot exceed balance due ({inv.balance_due})")

        payment = Payment(
            clinic_id=inv.clinic_id,
            invoice_id=inv.id,
            amount=pay_amount,
            payment_method=data.payment_method.upper(),
            transaction_reference=data.transaction_reference,
            notes=data.notes,
            created_by_user_id=actor_id,
        )
        db.add(payment)

        inv.amount_paid += pay_amount
        inv.balance_due -= pay_amount
        inv.payment_method = data.payment_method.upper()

        if inv.balance_due <= Decimal("0.01"):
            inv.status = "PAID"
            inv.balance_due = Decimal("0.00")
        else:
            inv.status = "PARTIALLY_PAID"

        db.commit()
        db.refresh(inv)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=inv.clinic_id,
            action="PAYMENT_COLLECT",
            entity_type="Invoice",
            entity_id=inv.id,
            details={
                "amount": float(pay_amount),
                "payment_method": data.payment_method,
                "status": inv.status,
            }
        )
        return BillingService._format_invoice(inv)

    @staticmethod
    def record_refund(
        db: Session,
        invoice_id: str,
        data: RefundCreate,
        clinic_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> InvoiceResponse:
        query = db.query(Invoice).filter(Invoice.id == invoice_id)
        if clinic_id:
            query = query.filter(Invoice.clinic_id == clinic_id)
        inv = query.first()
        if not inv:
            raise ValueError("Invoice not found or unauthorized")

        ref_amount = Decimal(str(round(data.amount, 2)))
        if ref_amount <= Decimal("0.00"):
            raise ValueError("Refund amount must be greater than zero")

        if ref_amount > inv.amount_paid:
            raise ValueError(f"Refund amount ({ref_amount}) cannot exceed collected amount ({inv.amount_paid})")

        refund = Refund(
            clinic_id=inv.clinic_id,
            invoice_id=inv.id,
            amount=ref_amount,
            reason=data.reason,
            status="APPROVED",
            processed_by_user_id=actor_id,
        )
        db.add(refund)

        inv.amount_paid -= ref_amount
        inv.balance_due += ref_amount

        if inv.amount_paid <= Decimal("0.01"):
            inv.status = "REFUNDED"
        else:
            inv.status = "PARTIALLY_PAID"

        db.commit()
        db.refresh(inv)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=inv.clinic_id,
            action="REFUND_PROCESSED",
            entity_type="Invoice",
            entity_id=inv.id,
            details={
                "amount": float(ref_amount),
                "reason": data.reason,
                "status": inv.status,
            }
        )
        return BillingService._format_invoice(inv)

    @staticmethod
    def get_invoices(
        db: Session,
        clinic_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[InvoiceResponse]:
        query = db.query(Invoice)
        if clinic_id:
            query = query.filter(Invoice.clinic_id == clinic_id)
        if patient_id:
            query = query.filter(Invoice.patient_id == patient_id)
        if status:
            query = query.filter(Invoice.status == status.upper())

        invoices = query.order_by(Invoice.created_at.desc()).all()
        return [BillingService._format_invoice(i) for i in invoices]

    @staticmethod
    def get_invoice_by_id(
        db: Session,
        invoice_id: str,
        clinic_id: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Optional[InvoiceResponse]:
        query = db.query(Invoice).filter(Invoice.id == invoice_id)
        if clinic_id:
            query = query.filter(Invoice.clinic_id == clinic_id)
        if patient_id:
            query = query.filter(Invoice.patient_id == patient_id)

        inv = query.first()
        if not inv:
            return None
        return BillingService._format_invoice(inv)

    @staticmethod
    def get_revenue_summary(db: Session, clinic_id: str) -> RevenueSummaryResponse:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # Payments query scoped to clinic
        all_payments = db.query(Payment).filter(Payment.clinic_id == clinic_id).all()
        all_refunds = db.query(Refund).filter(Refund.clinic_id == clinic_id).all()
        all_invoices = db.query(Invoice).filter(Invoice.clinic_id == clinic_id).all()

        today_rev = sum(float(p.amount) for p in all_payments if p.created_at >= today_start.replace(tzinfo=None))
        weekly_rev = sum(float(p.amount) for p in all_payments if p.created_at >= week_start.replace(tzinfo=None))
        monthly_rev = sum(float(p.amount) for p in all_payments if p.created_at >= month_start.replace(tzinfo=None))

        # Payment methods breakdown
        methods: Dict[str, float] = {}
        for p in all_payments:
            m = p.payment_method or "CASH"
            methods[m] = methods.get(m, 0.0) + float(p.amount)

        # Revenue by category (from invoice items on paid invoices)
        consult_rev = 0.0
        proc_rev = 0.0
        for inv in all_invoices:
            if inv.status in ["PAID", "PARTIALLY_PAID"]:
                for it in inv.items:
                    if it.item_type == "CONSULTATION":
                        consult_rev += float(it.total_price)
                    elif it.item_type == "PROCEDURE":
                        proc_rev += float(it.total_price)

        pending_dues = sum(float(i.balance_due) for i in all_invoices if i.status in ["PENDING", "PARTIALLY_PAID"])
        total_refunds = sum(float(r.amount) for r in all_refunds)

        total_rev = sum(float(p.amount) for p in all_payments)

        return RevenueSummaryResponse(
            total_revenue=round(total_rev, 2),
            today_revenue=round(today_rev, 2),
            weekly_revenue=round(weekly_rev, 2),
            monthly_revenue=round(monthly_rev, 2),
            consultation_revenue=round(consult_rev, 2),
            procedure_revenue=round(proc_rev, 2),
            payment_methods={k: round(v, 2) for k, v in methods.items()},
            pending_dues=round(pending_dues, 2),
            total_refunds=round(total_refunds, 2),
            invoice_count=len(all_invoices),
        )


billing_service = BillingService()
