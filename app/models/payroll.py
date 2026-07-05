from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    period_id: Mapped[int] = mapped_column(primary_key=True)
    period_type: Mapped[str] = mapped_column(String(30), default="WEEK")
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.site_id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("web_users.user_id"))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    line_items: Mapped[list["PayrollLineItem"]] = relationship(back_populates="period")


class PayrollLineItem(Base):
    __tablename__ = "payroll_line_items"

    line_item_id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.period_id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)
    days_present: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    half_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    days_absent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    daily_rate_override: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    overtime_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    advances: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    gross_wage: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    attendance_source: Mapped[str] = mapped_column(String(30), default="AUTO")
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    period: Mapped[PayrollPeriod] = relationship(back_populates="line_items")
    payments: Mapped[list["PayrollPayment"]] = relationship(back_populates="line_item")


class PayrollPayment(Base):
    __tablename__ = "payroll_payments"

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    line_item_id: Mapped[int] = mapped_column(ForeignKey("payroll_line_items.line_item_id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(100))
    recorded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("web_users.user_id"))
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    line_item: Mapped[PayrollLineItem] = relationship(back_populates="payments")


class PayrollAuditLog(Base):
    __tablename__ = "payroll_audit_log"

    audit_id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("payroll_periods.period_id"), nullable=False, index=True)
    line_item_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_line_items.line_item_id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("web_users.user_id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
