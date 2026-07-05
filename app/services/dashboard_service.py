from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.construction import (
    Attendance,
    AttendanceStatus,
    Employee,
    Expense,
    Material,
    MaterialTransaction,
    MaterialTransactionType,
    ProgressUpdate,
    Site,
    SiteStatus,
)
from app.models.payroll import PayrollPeriod
from app.schemas.dashboard import (
    AlertResponse,
    ChartSeriesResponse,
    DashboardOverviewResponse,
    InventoryRowResponse,
    SiteCardResponse,
)


class DashboardService:
    LOW_STOCK_THRESHOLD = Decimal("10")

    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self) -> DashboardOverviewResponse:
        today = date.today()
        active_sites = self.db.scalar(
            select(func.count(Site.site_id)).where(Site.status == SiteStatus.ACTIVE.value)
        ) or 0
        attendance_today = self.db.scalar(
            select(func.count(Attendance.attendance_id)).where(Attendance.attendance_date == today)
        ) or 0
        workers_today = self.db.scalar(
            select(func.count(func.distinct(Attendance.employee_id))).where(Attendance.attendance_date == today)
        ) or 0
        material_txn_today = self.db.scalar(
            select(func.count(MaterialTransaction.transaction_id)).where(MaterialTransaction.transaction_date == today)
        ) or 0
        expenses_today = self.db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.expense_date == today)
        ) or Decimal(0)
        open_periods = self.db.scalar(
            select(func.count(PayrollPeriod.period_id)).where(PayrollPeriod.status == "DRAFT")
        ) or 0

        return DashboardOverviewResponse(
            active_sites=active_sites,
            workers_today=workers_today,
            attendance_records_today=attendance_today,
            material_transactions_today=material_txn_today,
            expenses_today=Decimal(expenses_today),
            open_payroll_periods=open_periods,
        )

    def site_cards(self) -> list[SiteCardResponse]:
        today = date.today()
        sites = self.db.scalars(select(Site).order_by(Site.site_name)).all()
        cards: list[SiteCardResponse] = []

        for site in sites:
            workers_today = self.db.scalar(
                select(func.count(func.distinct(Attendance.employee_id))).where(
                    Attendance.site_id == site.site_id,
                    Attendance.attendance_date == today,
                )
            ) or 0
            spent = self.db.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.site_id == site.site_id)
            ) or Decimal(0)
            progress_count = self.db.scalar(
                select(func.count(ProgressUpdate.progress_id)).where(ProgressUpdate.site_id == site.site_id)
            ) or 0
            budget = site.project_budget
            used_percent = None
            if budget and budget > 0:
                used_percent = float((Decimal(spent) / Decimal(budget)) * 100)

            cards.append(
                SiteCardResponse(
                    site_id=site.site_id,
                    site_name=site.site_name,
                    status=site.status,
                    workers_today=workers_today,
                    budget_allocated=budget,
                    budget_spent=Decimal(spent),
                    budget_used_percent=used_percent,
                    progress_updates_count=progress_count,
                )
            )
        return cards

    def attendance_chart(self, days: int = 7) -> ChartSeriesResponse:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = self.db.execute(
            select(
                Site.site_name,
                Attendance.attendance_status,
                func.count(Attendance.attendance_id),
            )
            .join(Site, Site.site_id == Attendance.site_id)
            .where(Attendance.attendance_date >= start, Attendance.attendance_date <= end)
            .group_by(Site.site_name, Attendance.attendance_status)
            .order_by(Site.site_name)
        ).all()

        labels = sorted({site_name for site_name, _, _ in rows})
        statuses = [AttendanceStatus.PRESENT.value, AttendanceStatus.HALF_DAY.value, AttendanceStatus.ABSENT.value]
        lookup = {(site, status): count for site, status, count in rows}
        series = [
            {
                "name": status.title().replace("_", " "),
                "data": [lookup.get((label, status), 0) for label in labels],
            }
            for status in statuses
        ]
        return ChartSeriesResponse(labels=labels, series=series)

    def inventory_matrix(self) -> list[InventoryRowResponse]:
        sites = self.db.scalars(select(Site).order_by(Site.site_name)).all()
        materials = self.db.scalars(select(Material).order_by(Material.material_name)).all()
        rows: list[InventoryRowResponse] = []

        for site in sites:
            for material in materials:
                received = self.db.scalar(
                    select(func.coalesce(func.sum(MaterialTransaction.quantity), 0)).where(
                        MaterialTransaction.site_id == site.site_id,
                        MaterialTransaction.material_id == material.material_id,
                        MaterialTransaction.transaction_type == MaterialTransactionType.RECEIVED.value,
                    )
                ) or Decimal(0)
                consumed = self.db.scalar(
                    select(func.coalesce(func.sum(MaterialTransaction.quantity), 0)).where(
                        MaterialTransaction.site_id == site.site_id,
                        MaterialTransaction.material_id == material.material_id,
                        MaterialTransaction.transaction_type == MaterialTransactionType.CONSUMED.value,
                    )
                ) or Decimal(0)
                stock = Decimal(received) - Decimal(consumed)
                if stock == 0 and received == 0 and consumed == 0:
                    continue

                status = "OK"
                if stock <= 0:
                    status = "OUT"
                elif stock <= self.LOW_STOCK_THRESHOLD:
                    status = "LOW"

                rows.append(
                    InventoryRowResponse(
                        site_id=site.site_id,
                        site_name=site.site_name,
                        material_id=material.material_id,
                        material_name=material.material_name,
                        unit=material.unit,
                        stock_level=stock,
                        status=status,
                    )
                )
        return rows

    def budget_chart(self) -> ChartSeriesResponse:
        sites = self.db.scalars(select(Site).order_by(Site.site_name)).all()
        labels: list[str] = []
        allocated: list[float] = []
        spent: list[float] = []

        for site in sites:
            labels.append(site.site_name)
            allocated.append(float(site.project_budget or 0))
            site_spent = self.db.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.site_id == site.site_id)
            ) or Decimal(0)
            spent.append(float(site_spent))

        return ChartSeriesResponse(
            labels=labels,
            series=[
                {"name": "Allocated", "data": allocated},
                {"name": "Spent", "data": spent},
            ],
        )

    def material_consumption_trend(self, days: int = 30) -> ChartSeriesResponse:
        end = date.today()
        start = end - timedelta(days=days - 1)
        rows = self.db.execute(
            select(
                MaterialTransaction.transaction_date,
                func.coalesce(func.sum(MaterialTransaction.quantity), 0),
            )
            .where(
                MaterialTransaction.transaction_type == MaterialTransactionType.CONSUMED.value,
                MaterialTransaction.transaction_date >= start,
                MaterialTransaction.transaction_date <= end,
            )
            .group_by(MaterialTransaction.transaction_date)
            .order_by(MaterialTransaction.transaction_date)
        ).all()

        labels = [(start + timedelta(days=offset)).isoformat() for offset in range(days)]
        lookup = {row_date.isoformat(): float(qty) for row_date, qty in rows}
        data = [lookup.get(label, 0.0) for label in labels]
        return ChartSeriesResponse(labels=labels, series=[{"name": "Consumed quantity", "data": data}])

    def alerts(self) -> list[AlertResponse]:
        today = date.today()
        alerts: list[AlertResponse] = []

        for row in self.inventory_matrix():
            if row.status == "LOW":
                alerts.append(
                    AlertResponse(
                        alert_type="LOW_STOCK",
                        severity="warning",
                        message=f"{row.material_name} is low at {row.site_name} ({row.stock_level} {row.unit})",
                        site_id=row.site_id,
                    )
                )
            elif row.status == "OUT":
                alerts.append(
                    AlertResponse(
                        alert_type="OUT_OF_STOCK",
                        severity="critical",
                        message=f"{row.material_name} is out at {row.site_name}",
                        site_id=row.site_id,
                    )
                )

        active_sites = self.db.scalars(select(Site).where(Site.status == SiteStatus.ACTIVE.value)).all()
        for site in active_sites:
            count = self.db.scalar(
                select(func.count(Attendance.attendance_id)).where(
                    Attendance.site_id == site.site_id,
                    Attendance.attendance_date == today,
                )
            ) or 0
            if count == 0:
                alerts.append(
                    AlertResponse(
                        alert_type="MISSING_ATTENDANCE",
                        severity="warning",
                        message=f"No attendance recorded today for {site.site_name}",
                        site_id=site.site_id,
                    )
                )

            if site.project_budget and site.project_budget > 0:
                spent = self.db.scalar(
                    select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.site_id == site.site_id)
                ) or Decimal(0)
                if Decimal(spent) >= site.project_budget * Decimal("0.9"):
                    alerts.append(
                        AlertResponse(
                            alert_type="BUDGET_THRESHOLD",
                            severity="warning",
                            message=f"{site.site_name} has used 90%+ of budget",
                            site_id=site.site_id,
                        )
                    )

        return alerts
