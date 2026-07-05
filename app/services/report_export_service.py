import csv
import uuid
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.construction import Attendance, Employee, Expense, Site
from app.models.payroll import PayrollLineItem, PayrollPeriod
from app.services.analytics_tools import AnalyticsTools


class ReportExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analytics = AnalyticsTools(db)
        self.export_dir = Path(settings.report_export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        *,
        user_id: int,
        report_type: str,
        file_format: str,
        days: int = 7,
        report_date: str | None = None,
        period_id: int | None = None,
    ) -> dict:
        rows, headers, title = self._build_rows(report_type, days=days, report_date=report_date, period_id=period_id)
        report_id = str(uuid.uuid4())
        ext = "xlsx" if file_format == "xlsx" else "csv"
        filename = f"{report_type}_{date.today().isoformat()}_{report_id[:8]}.{ext}"
        path = self.export_dir / filename

        if file_format == "xlsx":
            self._write_xlsx(path, title, headers, rows)
        else:
            self._write_csv(path, headers, rows)

        download_url = f"/assistant/reports/{report_id}/download"
        meta_path = self.export_dir / f"{report_id}.json"
        meta_path.write_text(
            __import__("json").dumps(
                {
                    "report_id": report_id,
                    "filename": filename,
                    "file_path": str(path),
                    "user_id": user_id,
                    "report_type": report_type,
                    "format": file_format,
                }
            ),
            encoding="utf-8",
        )

        return {
            "report_id": report_id,
            "filename": filename,
            "format": file_format,
            "title": title,
            "row_count": len(rows),
            "download_url": download_url,
            "google_sheets_hint": "Upload the XLSX file to Google Drive → Open with Google Sheets, or File → Import in Google Sheets.",
        }

    def get_report_path(self, report_id: str, user_id: int) -> tuple[Path, str]:
        meta_path = self.export_dir / f"{report_id}.json"
        if not meta_path.exists():
            raise ValueError("Report not found.")
        meta = __import__("json").loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("user_id") != user_id:
            raise ValueError("You do not have access to this report.")
        return Path(meta["file_path"]), meta["filename"]

    def _build_rows(
        self,
        report_type: str,
        *,
        days: int,
        report_date: str | None,
        period_id: int | None,
    ) -> tuple[list[list], list[str], str]:
        if report_type == "daily_operations":
            payload = self.analytics.generate_daily_report(report_date or "today")
            headers = ["section", "detail"]
            rows = [
                ["report_date", payload["report_date"]],
                ["active_sites", str(payload["active_sites"])],
                ["expenses_total", payload["expenses_total"]],
                ["material_transactions", str(payload["material_transactions"])],
            ]
            for item in payload["attendance_breakdown"]:
                rows.append(["attendance", f"{item['site']} {item['status']} = {item['count']}"])
            for item in payload["progress_updates"]:
                rows.append(["progress", item["work_completed"]])
            for item in payload["alerts"]:
                rows.append(["alert", item["message"]])
            return rows, headers, f"Daily Operations {payload['report_date']}"

        if report_type == "attendance":
            chart = self.analytics.get_attendance_summary(days=days)
            headers = ["site"] + [s["name"] for s in chart["series"]]
            rows = []
            for idx, site in enumerate(chart["labels"]):
                rows.append([site] + [str(s["data"][idx]) for s in chart["series"]])
            return rows, headers, f"Attendance last {days} days"

        if report_type == "inventory":
            payload = self.analytics.get_inventory_summary()
            headers = ["site", "material", "unit", "stock", "status"]
            rows = [
                [r["site_name"], r["material_name"], r["unit"], str(r["stock_level"]), r["status"]]
                for r in payload["inventory"]
            ]
            return rows, headers, "Inventory by site"

        if report_type == "budget":
            chart = self.analytics.get_budget_summary()
            headers = ["site", "allocated", "spent"]
            rows = [
                [chart["labels"][i], str(chart["series"][0]["data"][i]), str(chart["series"][1]["data"][i])]
                for i in range(len(chart["labels"]))
            ]
            return rows, headers, "Budget utilization"

        if report_type == "payroll":
            summary = self.analytics.get_payroll_summary(period_id=period_id)
            pid = summary.get("period_id")
            if pid is None:
                return [["message", "No payroll period"]], ["field", "value"], "Payroll"
            lines = self.db.scalars(select(PayrollLineItem).where(PayrollLineItem.period_id == pid)).all()
            employees = {e.employee_id: e.full_name for e in self.db.scalars(select(Employee)).all()}
            headers = [
                "worker",
                "present",
                "half_days",
                "absent",
                "rate",
                "gross",
                "paid",
                "balance",
            ]
            rows = [
                [
                    employees.get(line.employee_id, str(line.employee_id)),
                    str(line.days_present),
                    str(line.half_days),
                    str(line.days_absent),
                    str(line.daily_rate_override or ""),
                    str(line.gross_wage),
                    str(line.amount_paid),
                    str(line.balance_due),
                ]
                for line in lines
            ]
            period = self.db.get(PayrollPeriod, pid)
            title = f"Payroll {period.period_start} to {period.period_end}" if period else "Payroll"
            return rows, headers, title

        raise ValueError(f"Unsupported report type: {report_type}")

    def _write_csv(self, path: Path, headers: list[str], rows: list[list]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)

    def _write_xlsx(self, path: Path, title: str, headers: list[str], rows: list[list]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Report"[:31]
        sheet.append([title])
        sheet.append([])
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        workbook.save(path)
