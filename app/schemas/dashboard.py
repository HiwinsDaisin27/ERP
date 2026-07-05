from decimal import Decimal

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    active_sites: int
    workers_today: int
    attendance_records_today: int
    material_transactions_today: int
    expenses_today: Decimal
    open_payroll_periods: int


class SiteCardResponse(BaseModel):
    site_id: int
    site_name: str
    status: str
    workers_today: int
    budget_allocated: Decimal | None
    budget_spent: Decimal
    budget_used_percent: float | None
    progress_updates_count: int


class ChartSeriesResponse(BaseModel):
    labels: list[str]
    series: list[dict[str, object]]


class InventoryRowResponse(BaseModel):
    site_id: int
    site_name: str
    material_id: int
    material_name: str
    unit: str
    stock_level: Decimal
    status: str


class AlertResponse(BaseModel):
    alert_type: str
    severity: str
    message: str
    site_id: int | None = None
