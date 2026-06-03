from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
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
    SiteAssignment,
    SiteStatus,
)
from app.models.telegram import TelegramWorkflowSession
from app.services.telegram_keyboards import main_menu_keyboard


@dataclass(frozen=True)
class WorkflowField:
    name: str
    prompt: str
    kind: str = "text"
    optional: bool = False


WORKFLOWS: dict[str, list[WorkflowField]] = {
    "add_site": [
        WorkflowField("site_name", "Site name?"),
        WorkflowField("location", "Location?"),
        WorkflowField("supervisor_name", "Supervisor name?", optional=True),
        WorkflowField("project_start_date", "Start date? Use YYYY-MM-DD, or type today.", "date", optional=True),
        WorkflowField("expected_end_date", "Expected end date? Use YYYY-MM-DD, or type skip.", "date", optional=True),
        WorkflowField("project_budget", "Project budget? Use a number, or type skip.", "decimal", optional=True),
    ],
    "add_worker": [
        WorkflowField("full_name", "Worker full name?"),
        WorkflowField("phone_number", "Phone number?", optional=True),
        WorkflowField("role", "Role? Example: Mason, Helper, Electrician.", optional=True),
        WorkflowField("wage_type", "Wage type? Type daily, weekly, or skip.", optional=True),
        WorkflowField("daily_rate", "Daily rate? Use a number, or type skip.", "decimal", optional=True),
        WorkflowField("weekly_rate", "Weekly rate? Use a number, or type skip.", "decimal", optional=True),
        WorkflowField("joining_date", "Joining date? Use YYYY-MM-DD, today, or skip.", "date", optional=True),
    ],
    "add_material": [
        WorkflowField("material_name", "Material name? Example: Cement."),
        WorkflowField("unit", "Unit? Example: bags, kg, tons, pieces."),
        WorkflowField("site_id", "Site ID for initial stock? Type /sites to view sites.", "int"),
        WorkflowField("quantity", "Initial quantity?", "decimal"),
        WorkflowField("transaction_date", "Date? Use YYYY-MM-DD or today.", "date"),
        WorkflowField("remarks", "Remarks? Type skip if none.", optional=True),
    ],
    "receive_material": [
        WorkflowField("site_id", "Site ID receiving material? Type /sites to view sites.", "int"),
        WorkflowField("material_name", "Material name? Existing or new."),
        WorkflowField("unit", "Unit if material is new? Type skip if already exists.", optional=True),
        WorkflowField("quantity", "Quantity received?", "decimal"),
        WorkflowField("supplier", "Supplier name? Type skip if unknown.", optional=True),
        WorkflowField("transaction_date", "Date? Use YYYY-MM-DD or today.", "date"),
    ],
    "consume_material": [
        WorkflowField("site_id", "Site ID consuming material? Type /sites to view sites.", "int"),
        WorkflowField("material_name", "Material name?"),
        WorkflowField("quantity", "Quantity consumed?", "decimal"),
        WorkflowField("transaction_date", "Date? Use YYYY-MM-DD or today.", "date"),
        WorkflowField("remarks", "Remarks? Type skip if none.", optional=True),
    ],
    "add_expense": [
        WorkflowField("site_id", "Site ID? Type /sites to view sites.", "int"),
        WorkflowField("expense_category", "Expense category? Example: Transport, Food, Equipment."),
        WorkflowField("amount", "Amount?", "decimal"),
        WorkflowField("description", "Description? Type skip if none.", optional=True),
        WorkflowField("expense_date", "Date? Use YYYY-MM-DD or today.", "date"),
    ],
    "progress_update": [
        WorkflowField("site_id", "Site ID? Type /sites to view sites.", "int"),
        WorkflowField("update_date", "Update date? Use YYYY-MM-DD or today.", "date"),
        WorkflowField("work_completed", "What work was completed?"),
        WorkflowField("remarks", "Notes/remarks? Type skip if none.", optional=True),
    ],
    "mark_attendance": [
        WorkflowField("site_id", "Site ID? Type /sites to view sites.", "int"),
        WorkflowField("attendance_date", "Attendance date? Use YYYY-MM-DD or today.", "date"),
        WorkflowField("present_employee_ids", "Present employee IDs separated by commas. Type /workers to view workers.", "int_list", optional=True),
        WorkflowField("absent_employee_ids", "Absent employee IDs separated by commas, or type skip.", "int_list", optional=True),
    ],
    "assign_workers": [
        WorkflowField("site_id", "Site ID? Type /sites to view sites.", "int"),
        WorkflowField("assignment_date", "Assignment date? Use YYYY-MM-DD or today.", "date"),
        WorkflowField("employee_ids", "Employee IDs separated by commas. Type /workers to view workers.", "int_list"),
        WorkflowField("assigned_by", "Assigned by? Type skip if not needed.", optional=True),
    ],
}


CALLBACK_TO_WORKFLOW = {
    "hr:add_worker": "add_worker",
    "hr:attendance": "mark_attendance",
    "hr:assign_workers": "assign_workers",
    "site:add_site": "add_site",
    "site:add_material": "add_material",
    "site:receive_material": "receive_material",
    "site:consume_material": "consume_material",
    "site:add_expense": "add_expense",
    "site:progress_update": "progress_update",
}


class WorkflowEngine:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start(self, chat_id: int, workflow_name: str) -> tuple[str, dict | None]:
        self.cancel_active(chat_id)
        first_field = WORKFLOWS[workflow_name][0]
        session = TelegramWorkflowSession(
            chat_id=chat_id,
            workflow_name=workflow_name,
            step=first_field.name,
            data={},
        )
        self.db.add(session)
        self.db.commit()
        return self._workflow_title(workflow_name) + "\n" + first_field.prompt, None

    def continue_with_text(self, chat_id: int, text: str) -> tuple[bool, str, dict | None]:
        session = self.active_session(chat_id)
        if session is None:
            return False, "", None

        if text.strip().lower() in {"/cancel", "cancel"}:
            session.status = "CANCELLED"
            self.db.commit()
            return True, "Cancelled. Choose the next operation:", main_menu_keyboard()

        fields = WORKFLOWS[session.workflow_name]
        index = self._field_index(session.workflow_name, session.step)
        field = fields[index]

        try:
            value = self._parse_value(field, text)
        except ValueError as exc:
            return True, f"{exc}\n\n{field.prompt}", None

        data = dict(session.data or {})
        data[field.name] = value
        session.data = data

        next_index = index + 1
        if next_index < len(fields):
            next_field = fields[next_index]
            session.step = next_field.name
            self.db.commit()
            return True, next_field.prompt, None

        try:
            result = self._commit_workflow(session.workflow_name, data)
        except ValueError as exc:
            self.db.rollback()
            return True, f"{exc}\n\nUse /cancel to exit, or send a corrected value by starting this workflow again.", main_menu_keyboard()
        except SQLAlchemyError as exc:
            self.db.rollback()
            return True, f"Database rejected this entry: {exc.__class__.__name__}. Check for duplicate values, then try again.", main_menu_keyboard()
        session.status = "COMPLETED"
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            return True, f"Database rejected this entry: {exc.__class__.__name__}. Check for duplicate phone numbers or invalid values, then try again.", main_menu_keyboard()
        return True, result + "\n\nChoose the next operation:", main_menu_keyboard()

    def active_session(self, chat_id: int) -> TelegramWorkflowSession | None:
        return self.db.scalar(
            select(TelegramWorkflowSession)
            .where(
                TelegramWorkflowSession.chat_id == chat_id,
                TelegramWorkflowSession.status == "ACTIVE",
            )
            .order_by(TelegramWorkflowSession.updated_at.desc())
        )

    def cancel_active(self, chat_id: int) -> None:
        sessions = self.db.scalars(
            select(TelegramWorkflowSession).where(
                TelegramWorkflowSession.chat_id == chat_id,
                TelegramWorkflowSession.status == "ACTIVE",
            )
        ).all()
        for session in sessions:
            session.status = "CANCELLED"

    def list_sites(self) -> str:
        sites = self.db.scalars(select(Site).order_by(Site.site_name)).all()
        if not sites:
            return "No sites found yet. Add a site first."
        lines = ["Sites:"]
        for site in sites:
            lines.append(f"{site.site_id}. {site.site_name} - {site.status}")
        return "\n".join(lines)

    def list_workers(self) -> str:
        workers = self.db.scalars(select(Employee).order_by(Employee.full_name)).all()
        if not workers:
            return "No workers found yet. Add workers first."
        lines = ["Workers:"]
        for worker in workers:
            label = f"{worker.employee_id}. {worker.full_name}"
            if worker.role:
                label += f" - {worker.role}"
            lines.append(label)
        return "\n".join(lines)

    def report_daily_attendance(self) -> str:
        today = date.today()
        rows = self.db.execute(
            select(Site.site_name, Attendance.attendance_status, func.count(Attendance.attendance_id))
            .join(Attendance, Attendance.site_id == Site.site_id)
            .where(Attendance.attendance_date == today)
            .group_by(Site.site_name, Attendance.attendance_status)
            .order_by(Site.site_name)
        ).all()
        if not rows:
            return f"No attendance records found for {today}."
        lines = [f"Daily attendance report - {today}"]
        for site_name, status, count in rows:
            lines.append(f"{site_name}: {status} = {count}")
        return "\n".join(lines)

    def report_daily_site(self) -> str:
        today = date.today()
        site_count = self.db.scalar(select(func.count(Site.site_id)).where(Site.status == SiteStatus.ACTIVE.value)) or 0
        expense_total = self.db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.expense_date == today)) or 0
        material_count = self.db.scalar(
            select(func.count(MaterialTransaction.transaction_id)).where(MaterialTransaction.transaction_date == today)
        ) or 0
        progress_count = self.db.scalar(select(func.count(ProgressUpdate.progress_id)).where(ProgressUpdate.update_date == today)) or 0
        return "\n".join(
            [
                f"Daily site report - {today}",
                f"Active sites: {site_count}",
                f"Material transactions today: {material_count}",
                f"Progress updates today: {progress_count}",
                f"Expenses today: {expense_total}",
            ]
        )

    def _commit_workflow(self, workflow_name: str, data: dict) -> str:
        if workflow_name == "add_site":
            site = Site(
                site_name=data["site_name"],
                location=data.get("location"),
                supervisor_name=data.get("supervisor_name"),
                project_start_date=self._as_date(data.get("project_start_date")),
                expected_end_date=self._as_date(data.get("expected_end_date")),
                project_budget=self._as_decimal(data.get("project_budget")),
            )
            self.db.add(site)
            self.db.flush()
            return f"Site added: {site.site_name} (ID {site.site_id})."

        if workflow_name == "add_worker":
            worker = Employee(
                full_name=data["full_name"],
                phone_number=data.get("phone_number"),
                role=data.get("role"),
                wage_type=(data.get("wage_type") or "").upper() or None,
                daily_rate=self._as_decimal(data.get("daily_rate")),
                weekly_rate=self._as_decimal(data.get("weekly_rate")),
                joining_date=self._as_date(data.get("joining_date")),
            )
            self.db.add(worker)
            self.db.flush()
            return f"Worker added: {worker.full_name} (ID {worker.employee_id})."

        if workflow_name == "add_material":
            self._require_site(data["site_id"])
            material = self._get_or_create_material(data["material_name"], data["unit"])
            txn = MaterialTransaction(
                site_id=data["site_id"],
                material_id=material.material_id,
                transaction_type=MaterialTransactionType.RECEIVED.value,
                quantity=self._as_decimal(data["quantity"]),
                transaction_date=self._as_date(data["transaction_date"]),
                remarks=data.get("remarks") or "Initial stock",
            )
            self.db.add(txn)
            return f"Material added and initial stock recorded: {material.material_name}."

        if workflow_name == "receive_material":
            self._require_site(data["site_id"])
            material = self._get_or_create_material(data["material_name"], data.get("unit") or "unit")
            remarks = f"Supplier: {data['supplier']}" if data.get("supplier") else None
            self.db.add(
                MaterialTransaction(
                    site_id=data["site_id"],
                    material_id=material.material_id,
                    transaction_type=MaterialTransactionType.RECEIVED.value,
                    quantity=self._as_decimal(data["quantity"]),
                    transaction_date=self._as_date(data["transaction_date"]),
                    remarks=remarks,
                )
            )
            return f"Material received: {data['quantity']} {material.unit} {material.material_name}."

        if workflow_name == "consume_material":
            self._require_site(data["site_id"])
            material = self._require_material(data["material_name"])
            self.db.add(
                MaterialTransaction(
                    site_id=data["site_id"],
                    material_id=material.material_id,
                    transaction_type=MaterialTransactionType.CONSUMED.value,
                    quantity=self._as_decimal(data["quantity"]),
                    transaction_date=self._as_date(data["transaction_date"]),
                    remarks=data.get("remarks"),
                )
            )
            return f"Material consumed: {data['quantity']} {material.unit} {material.material_name}."

        if workflow_name == "add_expense":
            self._require_site(data["site_id"])
            self.db.add(
                Expense(
                    site_id=data["site_id"],
                    expense_category=data["expense_category"],
                    amount=self._as_decimal(data["amount"]),
                    description=data.get("description"),
                    expense_date=self._as_date(data["expense_date"]),
                )
            )
            return f"Expense added: {data['expense_category']} - {data['amount']}."

        if workflow_name == "progress_update":
            self._require_site(data["site_id"])
            self.db.add(
                ProgressUpdate(
                    site_id=data["site_id"],
                    update_date=self._as_date(data["update_date"]),
                    work_completed=data["work_completed"],
                    remarks=data.get("remarks"),
                )
            )
            return "Progress update saved."

        if workflow_name == "mark_attendance":
            self._require_site(data["site_id"])
            created = 0
            for employee_id in data.get("present_employee_ids") or []:
                self._require_worker(employee_id)
                self.db.add(
                    Attendance(
                        employee_id=employee_id,
                        site_id=data["site_id"],
                        attendance_date=self._as_date(data["attendance_date"]),
                        attendance_status=AttendanceStatus.PRESENT.value,
                    )
                )
                created += 1
            for employee_id in data.get("absent_employee_ids") or []:
                self._require_worker(employee_id)
                self.db.add(
                    Attendance(
                        employee_id=employee_id,
                        site_id=data["site_id"],
                        attendance_date=self._as_date(data["attendance_date"]),
                        attendance_status=AttendanceStatus.ABSENT.value,
                    )
                )
                created += 1
            return f"Attendance saved for {created} workers."

        if workflow_name == "assign_workers":
            self._require_site(data["site_id"])
            for employee_id in data["employee_ids"]:
                self._require_worker(employee_id)
                self.db.add(
                    SiteAssignment(
                        employee_id=employee_id,
                        site_id=data["site_id"],
                        assignment_date=self._as_date(data["assignment_date"]),
                        assigned_by=data.get("assigned_by"),
                    )
                )
            return f"Assigned {len(data['employee_ids'])} workers to site {data['site_id']}."

        raise ValueError(f"Unsupported workflow: {workflow_name}")

    def _get_or_create_material(self, name: str, unit: str) -> Material:
        material = self.db.scalar(select(Material).where(func.lower(Material.material_name) == name.lower()))
        if material:
            return material
        material = Material(material_name=name, unit=unit or "unit")
        self.db.add(material)
        self.db.flush()
        return material

    def _require_material(self, name: str) -> Material:
        material = self.db.scalar(select(Material).where(func.lower(Material.material_name) == name.lower()))
        if material is None:
            raise ValueError(f"Material not found: {name}. Add it first.")
        return material

    def _require_site(self, site_id: int) -> Site:
        site = self.db.get(Site, site_id)
        if site is None:
            raise ValueError(f"Site ID {site_id} was not found.")
        return site

    def _require_worker(self, employee_id: int) -> Employee:
        worker = self.db.get(Employee, employee_id)
        if worker is None:
            raise ValueError(f"Worker ID {employee_id} was not found.")
        return worker

    def _parse_value(self, field: WorkflowField, raw_text: str):
        text = raw_text.strip()
        if field.optional and text.lower() in {"skip", "none", "na", "n/a", "-"}:
            return None
        if not text and field.optional:
            return None
        if not text:
            raise ValueError("This field is required.")

        if field.kind == "text":
            return text
        if field.kind == "int":
            try:
                return int(text)
            except ValueError as exc:
                raise ValueError("Please enter a whole number ID.") from exc
        if field.kind == "int_list":
            if field.optional and text.lower() in {"skip", "none", "na", "n/a", "-"}:
                return []
            try:
                return [int(part.strip()) for part in text.split(",") if part.strip()]
            except ValueError as exc:
                raise ValueError("Please enter IDs separated by commas, like 1,2,3.") from exc
        if field.kind == "decimal":
            try:
                return str(Decimal(text.replace(",", "")))
            except InvalidOperation as exc:
                raise ValueError("Please enter a valid number.") from exc
        if field.kind == "date":
            if text.lower() == "today":
                return date.today().isoformat()
            try:
                return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
            except ValueError as exc:
                raise ValueError("Please use YYYY-MM-DD, today, or skip if allowed.") from exc

        return text

    def _as_decimal(self, value: str | None) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value)

    def _as_date(self, value: str | None) -> date | None:
        if value is None:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()

    def _field_index(self, workflow_name: str, field_name: str) -> int:
        for index, field in enumerate(WORKFLOWS[workflow_name]):
            if field.name == field_name:
                return index
        raise ValueError(f"Unknown field {field_name} for workflow {workflow_name}")

    def _workflow_title(self, workflow_name: str) -> str:
        return workflow_name.replace("_", " ").title()
