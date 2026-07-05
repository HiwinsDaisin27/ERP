from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import WebUser
from app.models.construction import Attendance, AttendanceStatus, Employee
from app.models.payroll import PayrollAuditLog, PayrollLineItem, PayrollPayment, PayrollPeriod
from app.schemas.payroll import (
    CreatePayrollPeriodRequest,
    PayrollLineResponse,
    PayrollPaymentResponse,
    PayrollPeriodListItem,
    PayrollSummaryResponse,
    PayrollWorkbookResponse,
    RecordPayrollPaymentRequest,
    UpdatePayrollLineRequest,
)


class PayrollService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_periods(self) -> list[PayrollPeriodListItem]:
        periods = self.db.scalars(select(PayrollPeriod).order_by(PayrollPeriod.period_start.desc())).all()
        items: list[PayrollPeriodListItem] = []
        for period in periods:
            outstanding = self.db.scalar(
                select(func.coalesce(func.sum(PayrollLineItem.balance_due), 0)).where(
                    PayrollLineItem.period_id == period.period_id
                )
            ) or Decimal(0)
            items.append(
                PayrollPeriodListItem(
                    period_id=period.period_id,
                    period_type=period.period_type,
                    period_start=period.period_start,
                    period_end=period.period_end,
                    site_id=period.site_id,
                    status=period.status,
                    total_outstanding=Decimal(outstanding),
                )
            )
        return items

    def create_period(self, payload: CreatePayrollPeriodRequest, user: WebUser) -> PayrollWorkbookResponse:
        if payload.period_end < payload.period_start:
            raise ValueError("period_end must be on or after period_start.")

        site_filter = (
            PayrollPeriod.site_id.is_(None)
            if payload.site_id is None
            else PayrollPeriod.site_id == payload.site_id
        )
        overlap = self.db.scalar(
            select(PayrollPeriod.period_id).where(
                PayrollPeriod.status == "DRAFT",
                PayrollPeriod.period_start <= payload.period_end,
                PayrollPeriod.period_end >= payload.period_start,
                site_filter,
            )
        )
        if overlap:
            raise ValueError("A draft payroll period already overlaps this date range.")

        period = PayrollPeriod(
            period_type=payload.period_type,
            period_start=payload.period_start,
            period_end=payload.period_end,
            site_id=payload.site_id,
            notes=payload.notes,
            created_by_user_id=user.user_id,
        )
        self.db.add(period)
        self.db.flush()
        self._audit(period.period_id, user.user_id, "CREATE_PERIOD", None, None, f"{payload.period_start} to {payload.period_end}")
        self._ensure_line_items(period)
        self.recalculate_period(period.period_id, user, from_attendance=True)
        self.db.commit()
        return self.get_workbook(period.period_id)

    def get_workbook(self, period_id: int) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        lines = self.db.scalars(
            select(PayrollLineItem)
            .where(PayrollLineItem.period_id == period_id)
            .options(selectinload(PayrollLineItem.payments))
            .order_by(PayrollLineItem.line_item_id)
        ).all()
        employee_map = {
            employee.employee_id: employee
            for employee in self.db.scalars(select(Employee)).all()
        }

        line_responses: list[PayrollLineResponse] = []
        total_gross = Decimal(0)
        total_paid = Decimal(0)
        total_outstanding = Decimal(0)

        for line in lines:
            employee = employee_map[line.employee_id]
            effective_rate = line.daily_rate_override or employee.daily_rate or Decimal(0)
            line_responses.append(self._line_to_response(line, employee.full_name, effective_rate))
            total_gross += line.gross_wage
            total_paid += line.amount_paid
            total_outstanding += line.balance_due

        return PayrollWorkbookResponse(
            period_id=period.period_id,
            period_type=period.period_type,
            period_start=period.period_start,
            period_end=period.period_end,
            site_id=period.site_id,
            status=period.status,
            finalized_at=period.finalized_at,
            summary=PayrollSummaryResponse(
                total_gross=total_gross,
                total_paid=total_paid,
                total_outstanding=total_outstanding,
                worker_count=len(line_responses),
            ),
            lines=line_responses,
        )

    def recalculate_period(self, period_id: int, user: WebUser, *, from_attendance: bool = False) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        self._require_editable(period)

        if from_attendance:
            self._sync_attendance_into_lines(period)

        lines = self.db.scalars(select(PayrollLineItem).where(PayrollLineItem.period_id == period_id)).all()
        employee_map = {e.employee_id: e for e in self.db.scalars(select(Employee)).all()}

        for line in lines:
            employee = employee_map[line.employee_id]
            old_gross = line.gross_wage
            line.gross_wage = self._calculate_gross(line, employee)
            line.amount_paid = self._sum_payments(line.line_item_id)
            line.balance_due = line.gross_wage - line.amount_paid
            if old_gross != line.gross_wage:
                self._audit(
                    period_id,
                    user.user_id,
                    "RECALCULATE_LINE",
                    "gross_wage",
                    str(old_gross),
                    str(line.gross_wage),
                    line.line_item_id,
                )

        self._audit(period_id, user.user_id, "RECALCULATE_PERIOD", None, None, None)
        self.db.commit()
        return self.get_workbook(period_id)

    def update_line(
        self,
        period_id: int,
        line_item_id: int,
        payload: UpdatePayrollLineRequest,
        user: WebUser,
    ) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        self._require_editable(period)
        line = self._require_line(period_id, line_item_id)
        employee = self.db.get(Employee, line.employee_id)
        if employee is None:
            raise ValueError("Employee not found for line item.")

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            old = getattr(line, field)
            if old != value:
                self._audit(period_id, user.user_id, "UPDATE_LINE", field, str(old), str(value), line_item_id)
                setattr(line, field, value)

        if updates:
            line.attendance_source = "MANUAL"
            line.gross_wage = self._calculate_gross(line, employee)
            line.amount_paid = self._sum_payments(line.line_item_id)
            line.balance_due = line.gross_wage - line.amount_paid

        self.db.commit()
        return self.get_workbook(period_id)

    def record_payment(
        self,
        period_id: int,
        line_item_id: int,
        payload: RecordPayrollPaymentRequest,
        user: WebUser,
    ) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        self._require_editable(period)
        line = self._require_line(period_id, line_item_id)

        payment = PayrollPayment(
            line_item_id=line.line_item_id,
            amount=payload.amount,
            payment_date=payload.payment_date,
            payment_method=payload.payment_method,
            remarks=payload.remarks,
            recorded_by_user_id=user.user_id,
        )
        self.db.add(payment)
        self.db.flush()

        line.amount_paid = self._sum_payments(line.line_item_id)
        line.balance_due = line.gross_wage - line.amount_paid
        self._audit(
            period_id,
            user.user_id,
            "RECORD_PAYMENT",
            "amount_paid",
            None,
            str(payload.amount),
            line_item_id,
        )
        self.db.commit()
        return self.get_workbook(period_id)

    def mark_worker_paid(self, period_id: int, line_item_id: int, user: WebUser, payment_date: date | None = None) -> PayrollWorkbookResponse:
        line = self._require_line(period_id, line_item_id)
        remaining = line.balance_due
        if remaining <= 0:
            return self.get_workbook(period_id)

        return self.record_payment(
            period_id,
            line_item_id,
            RecordPayrollPaymentRequest(
                amount=remaining,
                payment_date=payment_date or date.today(),
                payment_method="Manual",
                remarks="Marked paid",
            ),
            user,
        )

    def mark_all_paid(self, period_id: int, user: WebUser, payment_date: date | None = None) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        self._require_editable(period)
        lines = self.db.scalars(select(PayrollLineItem).where(PayrollLineItem.period_id == period_id)).all()
        pay_date = payment_date or date.today()

        for line in lines:
            if line.balance_due <= 0:
                continue
            payment = PayrollPayment(
                line_item_id=line.line_item_id,
                amount=line.balance_due,
                payment_date=pay_date,
                payment_method="Bulk",
                remarks="Mark all paid",
                recorded_by_user_id=user.user_id,
            )
            self.db.add(payment)

        self.db.flush()
        for line in lines:
            line.amount_paid = self._sum_payments(line.line_item_id)
            line.balance_due = line.gross_wage - line.amount_paid

        self._audit(period_id, user.user_id, "MARK_ALL_PAID", None, None, pay_date.isoformat())
        self.db.commit()
        return self.get_workbook(period_id)

    def finalize_period(self, period_id: int, user: WebUser) -> PayrollWorkbookResponse:
        period = self._require_period(period_id)
        self._require_editable(period)
        period.status = "FINALIZED"
        period.finalized_at = datetime.now(timezone.utc)
        self._audit(period_id, user.user_id, "FINALIZE_PERIOD", "status", "DRAFT", "FINALIZED")
        self.db.commit()
        return self.get_workbook(period_id)

    def _ensure_line_items(self, period: PayrollPeriod) -> None:
        employees = self.db.scalars(
            select(Employee).where(Employee.status == "ACTIVE").order_by(Employee.full_name)
        ).all()
        existing = {
            line.employee_id
            for line in self.db.scalars(
                select(PayrollLineItem).where(PayrollLineItem.period_id == period.period_id)
            ).all()
        }

        for employee in employees:
            if employee.employee_id in existing:
                continue
            self.db.add(
                PayrollLineItem(
                    period_id=period.period_id,
                    employee_id=employee.employee_id,
                    daily_rate_override=employee.daily_rate,
                )
            )

    def _sync_attendance_into_lines(self, period: PayrollPeriod) -> None:
        lines = self.db.scalars(select(PayrollLineItem).where(PayrollLineItem.period_id == period.period_id)).all()
        for line in lines:
            if line.attendance_source == "MANUAL":
                continue

            query = select(Attendance).where(
                Attendance.employee_id == line.employee_id,
                Attendance.attendance_date >= period.period_start,
                Attendance.attendance_date <= period.period_end,
            )
            if period.site_id is not None:
                query = query.where(Attendance.site_id == period.site_id)

            records = self.db.scalars(query).all()
            present = sum(1 for r in records if r.attendance_status == AttendanceStatus.PRESENT.value)
            half = sum(1 for r in records if r.attendance_status == AttendanceStatus.HALF_DAY.value)
            absent = sum(1 for r in records if r.attendance_status == AttendanceStatus.ABSENT.value)
            overtime = sum((r.overtime_hours or Decimal(0)) for r in records)

            line.days_present = Decimal(present)
            line.half_days = Decimal(half)
            line.days_absent = Decimal(absent)
            line.overtime_hours = Decimal(overtime)
            line.attendance_source = "AUTO"

    def _calculate_gross(self, line: PayrollLineItem, employee: Employee) -> Decimal:
        rate = line.daily_rate_override or employee.daily_rate or Decimal(0)
        gross = (line.days_present * rate) + (line.half_days * rate * Decimal("0.5"))
        if line.overtime_hours:
            ot_rate = line.overtime_rate or rate
            gross += line.overtime_hours * ot_rate
        gross -= line.advances
        gross -= line.deductions
        return gross.quantize(Decimal("0.01"))

    def _sum_payments(self, line_item_id: int) -> Decimal:
        total = self.db.scalar(
            select(func.coalesce(func.sum(PayrollPayment.amount), 0)).where(
                PayrollPayment.line_item_id == line_item_id
            )
        ) or Decimal(0)
        return Decimal(total).quantize(Decimal("0.01"))

    def _line_to_response(
        self,
        line: PayrollLineItem,
        employee_name: str,
        effective_rate: Decimal,
    ) -> PayrollLineResponse:
        return PayrollLineResponse(
            line_item_id=line.line_item_id,
            employee_id=line.employee_id,
            employee_name=employee_name,
            days_present=line.days_present,
            half_days=line.half_days,
            days_absent=line.days_absent,
            daily_rate_override=line.daily_rate_override,
            effective_daily_rate=effective_rate,
            overtime_hours=line.overtime_hours,
            overtime_rate=line.overtime_rate,
            advances=line.advances,
            deductions=line.deductions,
            gross_wage=line.gross_wage,
            amount_paid=line.amount_paid,
            balance_due=line.balance_due,
            attendance_source=line.attendance_source,
            notes=line.notes,
            payments=[
                PayrollPaymentResponse(
                    payment_id=payment.payment_id,
                    amount=payment.amount,
                    payment_date=payment.payment_date,
                    payment_method=payment.payment_method,
                    remarks=payment.remarks,
                )
                for payment in line.payments
            ],
        )

    def _require_period(self, period_id: int) -> PayrollPeriod:
        period = self.db.get(PayrollPeriod, period_id)
        if period is None:
            raise ValueError(f"Payroll period #{period_id} not found.")
        return period

    def _require_line(self, period_id: int, line_item_id: int) -> PayrollLineItem:
        line = self.db.scalar(
            select(PayrollLineItem)
            .where(PayrollLineItem.period_id == period_id, PayrollLineItem.line_item_id == line_item_id)
            .options(selectinload(PayrollLineItem.payments))
        )
        if line is None:
            raise ValueError(f"Payroll line #{line_item_id} not found in period #{period_id}.")
        return line

    def _require_editable(self, period: PayrollPeriod) -> None:
        if period.status != "DRAFT":
            raise ValueError("This payroll period is finalized and cannot be edited.")

    def _audit(
        self,
        period_id: int,
        user_id: int,
        action: str,
        field_name: str | None,
        old_value: str | None,
        new_value: str | None,
        line_item_id: int | None = None,
    ) -> None:
        self.db.add(
            PayrollAuditLog(
                period_id=period_id,
                line_item_id=line_item_id,
                user_id=user_id,
                action=action,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
            )
        )
