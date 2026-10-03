from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True)

    subtotal = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    balance_due = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, PARTIALLY_PAID, PAID, REFUNDED, CANCELLED
    payment_method = Column(String(30), nullable=True)  # CASH, UPI, CARD, ONLINE_GATEWAY, BANK_TRANSFER
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    appointment = relationship("Appointment")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(50), default="CONSULTATION", nullable=False)  # CONSULTATION, PROCEDURE, LAB_TEST, MEDICINE, SERVICE
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_price = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(30), default="CASH", nullable=False)  # CASH, UPI, CARD, ONLINE_GATEWAY, BANK_TRANSFER
    transaction_reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    invoice = relationship("Invoice", back_populates="payments")
    created_by = relationship("User")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), default="APPROVED", nullable=False)  # REQUESTED, APPROVED, PROCESSED, REJECTED
    processed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    invoice = relationship("Invoice", back_populates="refunds")
    processed_by = relationship("User")
