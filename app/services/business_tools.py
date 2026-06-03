from datetime import date, datetime
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
)


def tool_schemas() -> list[dict]:
    return [
        {
            "name": "mark_attendance",
            "description": "Record attendance for one site on one date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "attendance_date": {"type": "string", "description": "YYYY-MM-DD or today"},
                    "present_worker_names": {"type": "array", "items": {"type": "string"}},
                    "absent_worker_names": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["site_name", "attendance_date"],
            },
        },
        {
            "name": "record_material_received",
            "description": "Record material received at a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "material_name": {"type": "string"},
                    "unit": {"type": "string"},
                    "quantity": {"type": "number"},
                    "supplier": {"type": "string"},
                    "transaction_date": {"type": "string", "description": "YYYY-MM-DD or today"},
                },
                "required": ["site_name", "material_name", "quantity", "transaction_date"],
            },
        },
        {
            "name": "record_material_consumed",
            "description": "Record material consumed at a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "material_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "transaction_date": {"type": "string", "description": "YYYY-MM-DD or today"},
                    "remarks": {"type": "string"},
                },
                "required": ["site_name", "material_name", "quantity", "transaction_date"],
            },
        },
        {
            "name": "record_site_expense",
            "description": "Record a non-payroll site expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "expense_category": {"type": "string"},
                    "amount": {"type": "number"},
                    "description": {"type": "string"},
                    "expense_date": {"type": "string", "description": "YYYY-MM-DD or today"},
                },
                "required": ["site_name", "expense_category", "amount", "expense_date"],
            },
        },
        {
            "name": "record_progress_update",
            "description": "Record daily work progress for a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "update_date": {"type": "string", "description": "YYYY-MM-DD or today"},
                    "work_completed": {"type": "string"},
                    "remarks": {"type": "string"},
                },
                "required": ["site_name", "update_date", "work_completed"],
            },
        },
    ]


class BusinessTools:
    def __init__(self, db: Session) -> None:
        self.db = db

    def mark_attendance(
        self,
        site_name: str,
        attendance_date: str,
        present_worker_names: list[str] | None = None,
        absent_worker_names: list[str] | None = None,
    ) -> dict:
        site = self._require_site_by_name(site_name)
        record_date = self._parse_date(attendance_date)
        created = 0

        for worker_name in present_worker_names or []:
            employee = self._require_employee_by_name(worker_name)
            self.db.add(
                Attendance(
                    employee_id=employee.employee_id,
                    site_id=site.site_id,
                    attendance_date=record_date,
                    attendance_status=AttendanceStatus.PRESENT.value,
                )
            )
            created += 1

        for worker_name in absent_worker_names or []:
            employee = self._require_employee_by_name(worker_name)
            self.db.add(
                Attendance(
                    employee_id=employee.employee_id,
                    site_id=site.site_id,
                    attendance_date=record_date,
                    attendance_status=AttendanceStatus.ABSENT.value,
                )
            )
            created += 1

        self.db.commit()
        return {"created": created, "site_id": site.site_id, "attendance_date": record_date.isoformat()}

    def record_material_received(
        self,
        site_name: str,
        material_name: str,
        quantity: int | float | str,
        transaction_date: str,
        unit: str | None = None,
        supplier: str | None = None,
    ) -> dict:
        site = self._require_site_by_name(site_name)
        material = self._get_or_create_material(material_name, unit or "unit")
        remarks = f"Supplier: {supplier}" if supplier else None
        transaction = self._record_material_transaction(
            site.site_id,
            material.material_id,
            MaterialTransactionType.RECEIVED.value,
            quantity,
            transaction_date,
            remarks,
        )
        self.db.commit()
        return {"transaction_id": transaction.transaction_id, "material_id": material.material_id}

    def record_material_consumed(
        self,
        site_name: str,
        material_name: str,
        quantity: int | float | str,
        transaction_date: str,
        remarks: str | None = None,
    ) -> dict:
        site = self._require_site_by_name(site_name)
        material = self._require_material_by_name(material_name)
        transaction = self._record_material_transaction(
            site.site_id,
            material.material_id,
            MaterialTransactionType.CONSUMED.value,
            quantity,
            transaction_date,
            remarks,
        )
        self.db.commit()
        return {"transaction_id": transaction.transaction_id, "material_id": material.material_id}

    def record_site_expense(
        self,
        site_name: str,
        expense_category: str,
        amount: int | float | str,
        expense_date: str,
        description: str | None = None,
    ) -> dict:
        site = self._require_site_by_name(site_name)
        expense = Expense(
            site_id=site.site_id,
            expense_category=expense_category,
            amount=Decimal(str(amount)),
            description=description,
            expense_date=self._parse_date(expense_date),
        )
        self.db.add(expense)
        self.db.commit()
        return {"expense_id": expense.expense_id}

    def record_progress_update(
        self,
        site_name: str,
        update_date: str,
        work_completed: str,
        remarks: str | None = None,
    ) -> dict:
        site = self._require_site_by_name(site_name)
        progress = ProgressUpdate(
            site_id=site.site_id,
            update_date=self._parse_date(update_date),
            work_completed=work_completed,
            remarks=remarks,
        )
        self.db.add(progress)
        self.db.commit()
        return {"progress_id": progress.progress_id}

    def _record_material_transaction(
        self,
        site_id: int,
        material_id: int,
        transaction_type: str,
        quantity: int | float | str,
        transaction_date: str,
        remarks: str | None,
    ) -> MaterialTransaction:
        transaction = MaterialTransaction(
            site_id=site_id,
            material_id=material_id,
            transaction_type=transaction_type,
            quantity=Decimal(str(quantity)),
            transaction_date=self._parse_date(transaction_date),
            remarks=remarks,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def _require_site_by_name(self, site_name: str) -> Site:
        site = self.db.scalar(select(Site).where(func.lower(Site.site_name) == site_name.lower()))
        if site is None:
            raise ValueError(f"Unknown site: {site_name}")
        return site

    def _require_employee_by_name(self, full_name: str) -> Employee:
        employee = self.db.scalar(select(Employee).where(func.lower(Employee.full_name) == full_name.lower()))
        if employee is None:
            raise ValueError(f"Unknown worker: {full_name}")
        return employee

    def _get_or_create_material(self, material_name: str, unit: str) -> Material:
        material = self.db.scalar(select(Material).where(func.lower(Material.material_name) == material_name.lower()))
        if material:
            return material
        material = Material(material_name=material_name, unit=unit)
        self.db.add(material)
        self.db.flush()
        return material

    def _require_material_by_name(self, material_name: str) -> Material:
        material = self.db.scalar(select(Material).where(func.lower(Material.material_name) == material_name.lower()))
        if material is None:
            raise ValueError(f"Unknown material: {material_name}")
        return material

    def _parse_date(self, value: str) -> date:
        if value.lower() == "today":
            return date.today()
        return datetime.strptime(value, "%Y-%m-%d").date()

