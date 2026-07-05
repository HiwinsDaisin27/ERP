import json
from datetime import date, datetime, timedelta
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
from app.models.payroll import PayrollLineItem, PayrollPeriod
from app.services.dashboard_service import DashboardService


def analytics_tool_schemas() -> list[dict]:
    return [
        {
            "name": "get_site_summary",
            "description": "Summary of all sites or one site by name.",
            "parameters": {
                "type": "object",
                "properties": {"site_name": {"type": "string"}},
            },
        },
        {
            "name": "get_attendance_summary",
            "description": "Attendance counts grouped by site for a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days back from today, default 7"},
                    "site_name": {"type": "string"},
                },
            },
        },
        {
            "name": "get_inventory_summary",
            "description": "Material stock levels per site.",
            "parameters": {
                "type": "object",
                "properties": {"site_name": {"type": "string"}},
            },
        },
        {
            "name": "get_budget_summary",
            "description": "Budget allocated vs expenses spent per site.",
            "parameters": {
                "type": "object",
                "properties": {"site_name": {"type": "string"}},
            },
        },
        {
            "name": "get_progress_summary",
            "description": "Recent progress updates for sites.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days back, default 7"},
                    "site_name": {"type": "string"},
                },
            },
        },
        {
            "name": "get_payroll_summary",
            "description": "Payroll workbook summary for latest or specific period.",
            "parameters": {
                "type": "object",
                "properties": {"period_id": {"type": "integer"}},
            },
        },
        {
            "name": "generate_daily_report",
            "description": "Structured daily operations snapshot for a date (YYYY-MM-DD or today).",
            "parameters": {
                "type": "object",
                "properties": {"report_date": {"type": "string", "description": "YYYY-MM-DD or today"}},
            },
        },
        {
            "name": "export_report_sheet",
            "description": "Export a spreadsheet report as CSV or XLSX. Returns a download link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": [
                            "daily_operations",
                            "attendance",
                            "inventory",
                            "budget",
                            "payroll",
                        ],
                    },
                    "format": {"type": "string", "enum": ["csv", "xlsx"], "description": "xlsx opens in Google Sheets"},
                    "days": {"type": "integer", "description": "For attendance/inventory context"},
                    "report_date": {"type": "string", "description": "For daily_operations, YYYY-MM-DD or today"},
                    "period_id": {"type": "integer", "description": "For payroll export"},
                },
                "required": ["report_type", "format"],
            },
        },
    ]


class AnalyticsTools:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dashboard = DashboardService(db)

    def build_entity_context(self) -> str:
        sites = self.db.scalars(select(Site.site_name).order_by(Site.site_name)).all()
        workers = self.db.scalars(select(Employee.full_name).order_by(Employee.full_name)).all()
        return "\n".join(
            [
                f"Sites: {', '.join(sites) if sites else 'none'}",
                f"Workers: {', '.join(workers) if workers else 'none'}",
                f"Today: {date.today().isoformat()}",
            ]
        )

    def call_tool(self, tool_name: str, arguments: dict, user_id: int) -> dict:
        from app.services.report_export_service import ReportExportService

        allowed = {
            "get_site_summary": self.get_site_summary,
            "get_attendance_summary": self.get_attendance_summary,
            "get_inventory_summary": self.get_inventory_summary,
            "get_budget_summary": self.get_budget_summary,
            "get_progress_summary": self.get_progress_summary,
            "get_payroll_summary": self.get_payroll_summary,
            "generate_daily_report": self.generate_daily_report,
        }
        if tool_name == "export_report_sheet":
            return ReportExportService(self.db).export(
                user_id=user_id,
                report_type=arguments["report_type"],
                file_format=arguments.get("format", "xlsx"),
                days=int(arguments.get("days") or 7),
                report_date=arguments.get("report_date"),
                period_id=arguments.get("period_id"),
            )

        tool = allowed.get(tool_name)
        if tool is None:
            raise ValueError(f"Unsupported analytics tool: {tool_name}")
        return tool(**arguments)

    def get_site_summary(self, site_name: str | None = None) -> dict:
        cards = self.dashboard.site_cards()
        if site_name:
            cards = [c for c in cards if c.site_name.lower() == site_name.lower()]
            if not cards:
                raise ValueError(f"Unknown site: {site_name}")
        return {"sites": [c.model_dump(mode="json") for c in cards]}

    def get_attendance_summary(self, days: int = 7, site_name: str | None = None) -> dict:
        chart = self.dashboard.attendance_chart(days=days)
        if site_name:
            idx = next((i for i, label in enumerate(chart.labels) if label.lower() == site_name.lower()), None)
            if idx is None:
                raise ValueError(f"Unknown site: {site_name}")
            chart = type(chart)(
                labels=[chart.labels[idx]],
                series=[{"name": s["name"], "data": [s["data"][idx]]} for s in chart.series],
            )
        return chart.model_dump(mode="json")

    def get_inventory_summary(self, site_name: str | None = None) -> dict:
        rows = self.dashboard.inventory_matrix()
        if site_name:
            rows = [r for r in rows if r.site_name.lower() == site_name.lower()]
        return {"inventory": [r.model_dump(mode="json") for r in rows]}

    def get_budget_summary(self, site_name: str | None = None) -> dict:
        chart = self.dashboard.budget_chart()
        if site_name:
            idx = next((i for i, label in enumerate(chart.labels) if label.lower() == site_name.lower()), None)
            if idx is None:
                raise ValueError(f"Unknown site: {site_name}")
            return {
                "site": chart.labels[idx],
                "allocated": chart.series[0]["data"][idx],
                "spent": chart.series[1]["data"][idx],
            }
        return chart.model_dump(mode="json")

    def get_progress_summary(self, days: int = 7, site_name: str | None = None) -> dict:
        end = date.today()
        start = end - timedelta(days=days - 1)
        query = (
            select(ProgressUpdate, Site.site_name)
            .join(Site, Site.site_id == ProgressUpdate.site_id)
            .where(ProgressUpdate.update_date >= start, ProgressUpdate.update_date <= end)
            .order_by(ProgressUpdate.update_date.desc())
        )
        if site_name:
            query = query.where(func.lower(Site.site_name) == site_name.lower())
        rows = self.db.execute(query).all()
        return {
            "updates": [
                {
                    "site_name": site_name_value,
                    "update_date": pu.update_date.isoformat(),
                    "work_completed": pu.work_completed,
                    "remarks": pu.remarks,
                }
                for pu, site_name_value in rows
            ]
        }

    def get_payroll_summary(self, period_id: int | None = None) -> dict:
        if period_id is None:
            period = self.db.scalar(select(PayrollPeriod).order_by(PayrollPeriod.period_start.desc()))
        else:
            period = self.db.get(PayrollPeriod, period_id)
        if period is None:
            return {"message": "No payroll periods found."}

        lines = self.db.scalars(select(PayrollLineItem).where(PayrollLineItem.period_id == period.period_id)).all()
        total_gross = sum((line.gross_wage for line in lines), Decimal(0))
        total_paid = sum((line.amount_paid for line in lines), Decimal(0))
        return {
            "period_id": period.period_id,
            "period_start": period.period_start.isoformat(),
            "period_end": period.period_end.isoformat(),
            "status": period.status,
            "worker_count": len(lines),
            "total_gross": str(total_gross),
            "total_paid": str(total_paid),
            "total_outstanding": str(total_gross - total_paid),
        }

    def generate_daily_report(self, report_date: str = "today") -> dict:
        record_date = self._parse_date(report_date)
        overview = self.dashboard.overview()
        attendance_rows = self.db.execute(
            select(Site.site_name, Attendance.attendance_status, func.count(Attendance.attendance_id))
            .join(Attendance, Attendance.site_id == Site.site_id)
            .where(Attendance.attendance_date == record_date)
            .group_by(Site.site_name, Attendance.attendance_status)
        ).all()
        expenses = self.db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.expense_date == record_date)
        ) or Decimal(0)
        material_count = self.db.scalar(
            select(func.count(MaterialTransaction.transaction_id)).where(
                MaterialTransaction.transaction_date == record_date
            )
        ) or 0
        progress = self.db.scalars(
            select(ProgressUpdate).where(ProgressUpdate.update_date == record_date).limit(20)
        ).all()
        return {
            "report_date": record_date.isoformat(),
            "active_sites": overview.active_sites,
            "attendance_breakdown": [
                {"site": site, "status": status, "count": count} for site, status, count in attendance_rows
            ],
            "expenses_total": str(expenses),
            "material_transactions": material_count,
            "progress_updates": [
                {"work_completed": item.work_completed, "remarks": item.remarks} for item in progress
            ],
            "alerts": [a.model_dump(mode="json") for a in self.dashboard.alerts()],
        }

    def _parse_date(self, value: str) -> date:
        if value.lower() == "today":
            return date.today()
        return datetime.strptime(value, "%Y-%m-%d").date()
