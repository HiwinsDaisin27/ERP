from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SiteStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"


class MaterialTransactionType(str, Enum):
    RECEIVED = "RECEIVED"
    CONSUMED = "CONSUMED"
    TRANSFERRED = "TRANSFERRED"
    RETURNED = "RETURNED"


class Site(Base):
    __tablename__ = "sites"

    site_id: Mapped[int] = mapped_column(primary_key=True)
    site_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(300))
    supervisor_name: Mapped[str | None] = mapped_column(String(200))
    project_start_date: Mapped[date | None] = mapped_column(Date)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    project_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(30), default=SiteStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="site")
    material_transactions: Mapped[list["MaterialTransaction"]] = relationship(back_populates="site")


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), unique=True)
    role: Mapped[str | None] = mapped_column(String(100))
    wage_type: Mapped[str | None] = mapped_column(String(50))
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    weekly_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    joining_date: Mapped[date | None] = mapped_column(Date)
    image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="employee")


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    attendance_status: Mapped[str] = mapped_column(String(30), nullable=False)
    overtime_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    remarks: Mapped[str | None] = mapped_column(Text)

    employee: Mapped[Employee] = relationship(back_populates="attendance_records")
    site: Mapped[Site] = relationship(back_populates="attendance_records")


class SiteAssignment(Base):
    __tablename__ = "site_assignments"

    assignment_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id"), nullable=False, index=True)
    assignment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    assigned_by: Mapped[str | None] = mapped_column(String(200))


class Material(Base):
    __tablename__ = "materials"

    material_id: Mapped[int] = mapped_column(primary_key=True)
    material_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class MaterialTransaction(Base):
    __tablename__ = "material_transactions"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id"), nullable=False, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.material_id"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    site: Mapped[Site] = relationship(back_populates="material_transactions")


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id"), nullable=False, index=True)
    expense_category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    payroll_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    working_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    calculated_wage: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="PENDING")


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(100))
    remarks: Mapped[str | None] = mapped_column(Text)


class ProgressUpdate(Base):
    __tablename__ = "progress_updates"

    progress_id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id"), nullable=False, index=True)
    update_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    work_completed: Mapped[str] = mapped_column(Text, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
