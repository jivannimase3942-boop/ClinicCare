from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from app.models.pharmacy import Supplier, StockBatch, StockTransaction
from app.models.prescription import Medicine, Prescription
from app.models.billing import Invoice, InvoiceItem, Payment
from app.models.user import Patient, User
from app.schemas.pharmacy import (
    SupplierCreate,
    SupplierResponse,
    StockBatchCreate,
    StockBatchResponse,
    StockAdjustmentCreate,
    StockTransactionResponse,
    StockAlertItemResponse,
    PharmacyDispenseRequest,
    PharmacyDispenseResponse,
)
from app.services.audit_service import audit_service


class PharmacyService:
    @staticmethod
    def generate_invoice_number(db: Session) -> str:
        now = datetime.now(timezone.utc)
        prefix = f"INV-{now.strftime('%Y%m')}-"
        count = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).count()
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def _format_batch(b: StockBatch) -> StockBatchResponse:
        today = date.today()
        is_expired = b.expiry_date < today
        is_near_expiry = not is_expired and (b.expiry_date <= today + timedelta(days=60))
        is_low_stock = b.current_quantity <= b.reorder_threshold

        med_name = b.medicine.brand_name if b.medicine else None
        gen_name = b.medicine.generic_name if b.medicine else None
        dos_form = b.medicine.dosage_form if b.medicine else None
        sup_name = b.supplier.name if b.supplier else None

        return StockBatchResponse(
            id=b.id,
            clinic_id=b.clinic_id,
            medicine_id=b.medicine_id,
            medicine_name=med_name,
            generic_name=gen_name,
            dosage_form=dos_form,
            supplier_id=b.supplier_id,
            supplier_name=sup_name,
            batch_number=b.batch_number,
            expiry_date=b.expiry_date,
            purchase_price=b.purchase_price,
            mrp=b.mrp,
            sale_price=b.sale_price,
            initial_quantity=b.initial_quantity,
            current_quantity=b.current_quantity,
            reorder_threshold=b.reorder_threshold,
            is_active=b.is_active,
            is_expired=is_expired,
            is_near_expiry=is_near_expiry,
            is_low_stock=is_low_stock,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )

    # --- Supplier Operations ---

    @staticmethod
    def create_supplier(
        db: Session,
        clinic_id: str,
        data: SupplierCreate,
        actor_id: str
    ) -> SupplierResponse:
        supplier = Supplier(
            clinic_id=clinic_id,
            name=data.name,
            contact_person=data.contact_person,
            phone=data.phone,
            email=data.email,
            gstin=data.gstin,
            dl_number=data.dl_number,
            address=data.address,
            is_active=True,
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PHARMACY_SUPPLIER_CREATE",
            entity_type="Supplier",
            entity_id=supplier.id,
            details={"name": supplier.name, "gstin": supplier.gstin}
        )
        return SupplierResponse.model_validate(supplier)

    @staticmethod
    def list_suppliers(db: Session, clinic_id: str) -> List[SupplierResponse]:
        suppliers = db.query(Supplier).filter(
            Supplier.clinic_id == clinic_id,
            Supplier.is_active == True
        ).order_by(Supplier.name).all()
        return [SupplierResponse.model_validate(s) for s in suppliers]

    # --- Batch Operations ---

    @staticmethod
    def create_batch(
        db: Session,
        clinic_id: str,
        data: StockBatchCreate,
        actor_id: str
    ) -> StockBatchResponse:
        medicine = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
        if not medicine:
            raise ValueError("Medicine not found in catalog")

        if medicine.clinic_id and medicine.clinic_id != clinic_id:
            raise ValueError("Medicine does not belong to this clinic catalog")

        if data.supplier_id:
            sup = db.query(Supplier).filter(
                Supplier.id == data.supplier_id,
                Supplier.clinic_id == clinic_id
            ).first()
            if not sup:
                raise ValueError("Supplier not found for this clinic")

        batch = StockBatch(
            clinic_id=clinic_id,
            medicine_id=data.medicine_id,
            supplier_id=data.supplier_id,
            batch_number=data.batch_number.upper(),
            expiry_date=data.expiry_date,
            purchase_price=data.purchase_price,
            mrp=data.mrp,
            sale_price=data.sale_price,
            initial_quantity=data.initial_quantity,
            current_quantity=data.initial_quantity,
            reorder_threshold=data.reorder_threshold,
            is_active=True,
        )
        db.add(batch)
        db.flush()

        # Record inbound purchase transaction
        tx = StockTransaction(
            clinic_id=clinic_id,
            batch_id=batch.id,
            medicine_id=batch.medicine_id,
            transaction_type="PURCHASE",
            quantity=data.initial_quantity,
            balance_after=data.initial_quantity,
            unit_price=data.purchase_price,
            reason="Initial stock inbound from supplier",
            actor_user_id=actor_id,
        )
        db.add(tx)
        db.commit()
        db.refresh(batch)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PHARMACY_BATCH_CREATE",
            entity_type="StockBatch",
            entity_id=batch.id,
            details={
                "batch_number": batch.batch_number,
                "medicine": medicine.brand_name,
                "quantity": batch.initial_quantity,
                "expiry": str(batch.expiry_date),
            }
        )
        return PharmacyService._format_batch(batch)

    @staticmethod
    def list_batches(
        db: Session,
        clinic_id: str,
        medicine_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[StockBatchResponse]:
        query = db.query(StockBatch).filter(StockBatch.clinic_id == clinic_id)
        if medicine_id:
            query = query.filter(StockBatch.medicine_id == medicine_id)
        if active_only:
            query = query.filter(StockBatch.is_active == True)
        batches = query.order_by(StockBatch.expiry_date.asc()).all()
        return [PharmacyService._format_batch(b) for b in batches]

    @staticmethod
    def get_stock_alerts(db: Session, clinic_id: str) -> List[StockAlertItemResponse]:
        today = date.today()
        near_expiry_cutoff = today + timedelta(days=60)
        batches = db.query(StockBatch).filter(
            StockBatch.clinic_id == clinic_id,
            StockBatch.is_active == True,
            StockBatch.current_quantity > 0
        ).all()

        alerts = []
        for b in batches:
            med_name = b.medicine.brand_name if b.medicine else "Medicine"
            if b.expiry_date < today:
                alerts.append(StockAlertItemResponse(
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    medicine_id=b.medicine_id,
                    medicine_name=med_name,
                    expiry_date=b.expiry_date,
                    current_quantity=b.current_quantity,
                    reorder_threshold=b.reorder_threshold,
                    alert_type="EXPIRED",
                    severity="HIGH",
                    message=f"Expired on {b.expiry_date}. DO NOT DISPENSE.",
                ))
            elif b.expiry_date <= near_expiry_cutoff:
                days_left = (b.expiry_date - today).days
                alerts.append(StockAlertItemResponse(
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    medicine_id=b.medicine_id,
                    medicine_name=med_name,
                    expiry_date=b.expiry_date,
                    current_quantity=b.current_quantity,
                    reorder_threshold=b.reorder_threshold,
                    alert_type="NEAR_EXPIRY",
                    severity="MEDIUM",
                    message=f"Expires in {days_left} days ({b.expiry_date}). Prioritize FEFO dispensing.",
                ))

            if b.current_quantity <= b.reorder_threshold:
                alerts.append(StockAlertItemResponse(
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    medicine_id=b.medicine_id,
                    medicine_name=med_name,
                    expiry_date=b.expiry_date,
                    current_quantity=b.current_quantity,
                    reorder_threshold=b.reorder_threshold,
                    alert_type="LOW_STOCK",
                    severity="MEDIUM",
                    message=f"Low stock: {b.current_quantity} remaining (Reorder threshold: {b.reorder_threshold}).",
                ))

        return alerts

    # --- Auditable Stock Adjustments ---

    @staticmethod
    def adjust_stock(
        db: Session,
        clinic_id: str,
        data: StockAdjustmentCreate,
        actor_id: str
    ) -> StockBatchResponse:
        batch = db.query(StockBatch).filter(
            StockBatch.id == data.batch_id,
            StockBatch.clinic_id == clinic_id
        ).first()
        if not batch:
            raise ValueError("Stock batch not found or unauthorized")

        new_balance = batch.current_quantity + data.quantity
        if new_balance < 0:
            raise ValueError(f"Cannot adjust stock below 0. Current: {batch.current_quantity}, Delta: {data.quantity}")

        batch.current_quantity = new_balance

        tx = StockTransaction(
            clinic_id=clinic_id,
            batch_id=batch.id,
            medicine_id=batch.medicine_id,
            transaction_type=data.transaction_type.upper(),
            quantity=data.quantity,
            balance_after=new_balance,
            unit_price=data.unit_price or batch.sale_price,
            reason=data.reason,
            actor_user_id=actor_id,
        )
        db.add(tx)
        db.commit()
        db.refresh(batch)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PHARMACY_STOCK_ADJUSTMENT",
            entity_type="StockBatch",
            entity_id=batch.id,
            details={
                "type": data.transaction_type,
                "delta": data.quantity,
                "new_balance": new_balance,
                "reason": data.reason,
            }
        )
        return PharmacyService._format_batch(batch)

    @staticmethod
    def list_transactions(
        db: Session,
        clinic_id: str,
        batch_id: Optional[str] = None,
        medicine_id: Optional[str] = None,
        limit: int = 100
    ) -> List[StockTransactionResponse]:
        query = db.query(StockTransaction).filter(StockTransaction.clinic_id == clinic_id)
        if batch_id:
            query = query.filter(StockTransaction.batch_id == batch_id)
        if medicine_id:
            query = query.filter(StockTransaction.medicine_id == medicine_id)

        txs = query.order_by(desc(StockTransaction.created_at)).limit(limit).all()
        results = []
        for t in txs:
            b_num = t.batch.batch_number if t.batch else None
            m_name = t.medicine.brand_name if t.medicine else None
            act_name = t.actor.full_name if t.actor else None
            results.append(StockTransactionResponse(
                id=t.id,
                clinic_id=t.clinic_id,
                batch_id=t.batch_id,
                batch_number=b_num,
                medicine_id=t.medicine_id,
                medicine_name=m_name,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                balance_after=t.balance_after,
                unit_price=t.unit_price,
                invoice_id=t.invoice_id,
                prescription_id=t.prescription_id,
                reason=t.reason,
                actor_name=act_name,
                created_at=t.created_at,
            ))
        return results

    # --- Pharmacy Dispense & Billing Engine Integration ---

    @staticmethod
    def dispense_and_bill(
        db: Session,
        clinic_id: str,
        data: PharmacyDispenseRequest,
        actor_id: str
    ) -> PharmacyDispenseResponse:
        patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        today = date.today()
        batches_to_update = []
        total_subtotal = Decimal("0.00")

        # 1. Strict validation of all batches before modifying state
        for item in data.items:
            batch = db.query(StockBatch).filter(
                StockBatch.id == item.batch_id,
                StockBatch.clinic_id == clinic_id
            ).first()
            if not batch:
                raise ValueError(f"Batch {item.batch_id} not found or unauthorized")

            if batch.expiry_date < today:
                raise ValueError(
                    f"Safety Violation: Cannot dispense expired stock! "
                    f"Medicine '{batch.medicine.brand_name}' Batch '{batch.batch_number}' expired on {batch.expiry_date}."
                )

            if batch.current_quantity < item.quantity:
                raise ValueError(
                    f"Insufficient stock for '{batch.medicine.brand_name}' Batch '{batch.batch_number}'. "
                    f"Requested {item.quantity}, only {batch.current_quantity} available."
                )

            item_total = Decimal(str(batch.sale_price)) * Decimal(str(item.quantity))
            total_subtotal += item_total
            batches_to_update.append((batch, item.quantity, item_total))

        # 2. Create Invoice in existing billing system
        inv_number = PharmacyService.generate_invoice_number(db)
        is_paid_now = data.payment_method.upper() in ["CASH", "UPI", "CARD"]
        amount_paid = total_subtotal if is_paid_now else Decimal("0.00")
        balance_due = Decimal("0.00") if is_paid_now else total_subtotal
        inv_status = "PAID" if is_paid_now else "PENDING"

        invoice = Invoice(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            invoice_number=inv_number,
            subtotal=total_subtotal,
            discount_amount=Decimal("0.00"),
            tax_rate_percent=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=total_subtotal,
            amount_paid=amount_paid,
            balance_due=balance_due,
            status=inv_status,
            payment_method=data.payment_method.upper(),
            notes=data.notes or "Pharmacy Dispense & Prescription Fulfillment",
        )
        db.add(invoice)
        db.flush()

        # 3. Create InvoiceItems, deduct stock, and create auditable StockTransactions
        for batch, qty, line_total in batches_to_update:
            # Invoice Item
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                item_type="MEDICINE",
                description=f"{batch.medicine.brand_name} ({batch.medicine.generic_name}) - Batch: {batch.batch_number}",
                quantity=qty,
                unit_price=Decimal(str(batch.sale_price)),
                total_price=line_total,
            )
            db.add(inv_item)

            # Deduct stock
            new_balance = batch.current_quantity - qty
            batch.current_quantity = new_balance

            # Stock Transaction
            tx = StockTransaction(
                clinic_id=clinic_id,
                batch_id=batch.id,
                medicine_id=batch.medicine_id,
                transaction_type="SALE",
                quantity=-qty,
                balance_after=new_balance,
                unit_price=batch.sale_price,
                invoice_id=invoice.id,
                prescription_id=data.prescription_id,
                reason=f"Dispensed to patient {patient.user.full_name if patient.user else ''} (Inv: {inv_number})",
                actor_user_id=actor_id,
            )
            db.add(tx)

        # 4. If paid now, record Payment entry in existing payment ledger
        if is_paid_now and total_subtotal > Decimal("0.00"):
            payment = Payment(
                clinic_id=clinic_id,
                invoice_id=invoice.id,
                amount=total_subtotal,
                payment_method=data.payment_method.upper(),
                transaction_reference=f"PHARM-{inv_number}",
                notes="Immediate pharmacy counter settlement",
                created_by_user_id=actor_id,
            )
            db.add(payment)

        db.commit()
        db.refresh(invoice)

        audit_service.log_action(
            db=db,
            user_id=actor_id,
            clinic_id=clinic_id,
            action="PHARMACY_DISPENSE_SALE",
            entity_type="Invoice",
            entity_id=invoice.id,
            details={
                "invoice_number": inv_number,
                "total_amount": float(total_subtotal),
                "items_count": len(data.items),
                "payment_status": inv_status,
            }
        )

        return PharmacyDispenseResponse(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            total_amount=float(total_subtotal),
            status=invoice.status,
            items_dispensed=len(data.items),
            message="Medicines dispensed, inventory deducted, and invoice generated successfully",
        )


pharmacy_service = PharmacyService()
