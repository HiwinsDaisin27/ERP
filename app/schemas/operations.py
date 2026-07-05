from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class SiteCreateRequest(BaseModel):
    site_name: str = Field(min_length=2, max_length=200)
    location: str = Field(min_length=2, max_length=300)
    supervisor_name: str = Field(min_length=2, max_length=200)
    project_start_date: date
    expected_end_date: date | None = None
    project_budget: Decimal | None = Field(default=None, ge=0)
    status: str = "ACTIVE"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return normalized


class SiteResponse(BaseModel):
    site_id: int
    site_name: str
    location: str | None
    supervisor_name: str | None
    project_start_date: date | None
    expected_end_date: date | None
    project_budget: Decimal | None
    status: str


class WorkerCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    phone_number: str | None = Field(default=None, max_length=30)
    role: str = Field(min_length=2, max_length=100)
    wage_type: str = Field(min_length=2, max_length=50)
    daily_rate: Decimal | None = Field(default=None, ge=0)
    weekly_rate: Decimal | None = Field(default=None, ge=0)
    joining_date: date
    image_url: str | None = Field(default=None, max_length=500)
    status: str = "ACTIVE"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"ACTIVE", "INACTIVE"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("wage_type")
    @classmethod
    def validate_wage_type(cls, value: str) -> str:
        allowed = {"DAILY", "WEEKLY", "MONTHLY", "CONTRACT"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"Wage type must be one of: {', '.join(sorted(allowed))}")
        return normalized


class WorkerResponse(BaseModel):
    employee_id: int
    full_name: str
    phone_number: str | None
    role: str | None
    wage_type: str | None
    daily_rate: Decimal | None
    weekly_rate: Decimal | None
    joining_date: date | None
    image_url: str | None
    status: str


class AttendanceHistoryItem(BaseModel):
    attendance_id: int
    site_id: int
    site_name: str
    attendance_date: date
    attendance_status: str
    overtime_hours: Decimal | None
    remarks: str | None


class PayrollHistoryItem(BaseModel):
    period_id: int
    period_start: date
    period_end: date
    status: str
    gross_wage: Decimal
    amount_paid: Decimal
    balance_due: Decimal


class WorkerProfileResponse(BaseModel):
    worker: WorkerResponse
    attendance: list[AttendanceHistoryItem]
    payroll: list[PayrollHistoryItem]
