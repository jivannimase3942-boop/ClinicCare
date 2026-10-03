from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Date as SqlDate
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import generate_uuid, utc_now


class Supplier(Base):
    """
    Pharmacy medicine and clinical consumable supplier master.
    """
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    gstin = Column(String(50), nullable=True)  # GST Identification Number (India)
    dl_number = Column(String(100), nullable=True)  # State Drug License Number
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")
    batches = relationship("StockBatch", back_populates="supplier")


class StockBatch(Base):
    """
    Batch & Expiry tracking for pharmacy medicines.
    Ensures FIFO / FEFO (First-Expiry-First-Out) readiness and regulatory compliance.
    """
    __tablename__ = "stock_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(String(36), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)

    batch_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(SqlDate, nullable=False, index=True)
    purchase_price = Column(Float, nullable=False, default=0.0)
    mrp = Column(Float, nullable=False, default=0.0)
    sale_price = Column(Float, nullable=False, default=0.0)

    initial_quantity = Column(Integer, nullable=False, default=0)
    current_quantity = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, default=20, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    clinic = relationship("Clinic")
    medicine = relationship("Medicine")
    supplier = relationship("Supplier", back_populates="batches")
    transactions = relationship("StockTransaction", back_populates="batch", cascade="all, delete-orphan")


class StockTransaction(Base):
    """
    Auditable inventory movement ledger.
    Every stock adjustment, purchase, sale, damage, and return is permanently recorded.
    """
    __tablename__ = "stock_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    clinic_id = Column(String(36), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("stock_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(String(36), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)

    transaction_type = Column(String(50), nullable=False, index=True)  # PURCHASE, SALE, ISSUE, RETURN, DAMAGE, ADJUSTMENT, TRANSFER
    quantity = Column(Integer, nullable=False)  # delta quantity (+ for inbound, - for outbound)
    balance_after = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)

    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=True)

    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    clinic = relationship("Clinic")
    batch = relationship("StockBatch", back_populates="transactions")
    medicine = relationship("Medicine")
    actor = relationship("User")
    invoice = relationship("Invoice")
    prescription = relationship("Prescription")
