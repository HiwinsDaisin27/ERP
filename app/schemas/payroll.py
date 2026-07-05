from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreatePayrollPeriodRequest(BaseModel):
    period_type: str = Field(default="WEEK", pattern="^(WEEK|FORTNIGHT|MONTH)$")
    period_start: date
    period_end: date
    site_id: int | None = None
    notes: str | None = None


class UpdatePayrollLineRequest(BaseModel):
    days_present: Decimal | None = None
    half_days: Decimal | None = None
    days_absent: Decimal | None = None
    daily_rate_override: Decimal | None = None
    overtime_hours: Decimal | None = None
    overtime_rate: Decimal | None = None
    advances: Decimal | None = None
    deductions: Decimal | None = None
    notes: str | None = None


class RecordPayrollPaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_date: date
    payment_method: str | None = None
    remarks: str | None = None


class PayrollPaymentResponse(BaseModel):
    payment_id: int
    amount: Decimal
    payment_date: date
    payment_method: str | None
    remarks: str | None


class PayrollLineResponse(BaseModel):
    line_item_id: int
    employee_id: int
    employee_name: str
    days_present: Decimal
    half_days: Decimal
    days_absent: Decimal
    daily_rate_override: Decimal | None
    effective_daily_rate: Decimal
    overtime_hours: Decimal
    overtime_rate: Decimal | None
    advances: Decimal
    deductions: Decimal
    gross_wage: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    attendance_source: str
    notes: str | None
    payments: list[PayrollPaymentResponse]


class PayrollSummaryResponse(BaseModel):
    total_gross: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    worker_count: int


class PayrollWorkbookResponse(BaseModel):
    period_id: int
    period_type: str
    period_start: date
    period_end: date
    site_id: int | None
    status: str
    finalized_at: datetime | None
    summary: PayrollSummaryResponse
    lines: list[PayrollLineResponse]


class PayrollPeriodListItem(BaseModel):
    period_id: int
    period_type: str
    period_start: date
    period_end: date
    site_id: int | None
    status: str
    total_outstanding: Decimal
