from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.auth import WebUser
from app.schemas.payroll import (
    CreatePayrollPeriodRequest,
    PayrollPeriodListItem,
    PayrollWorkbookResponse,
    RecordPayrollPaymentRequest,
    UpdatePayrollLineRequest,
)
from app.services.payroll_service import PayrollService

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.get("/periods", response_model=list[PayrollPeriodListItem])
def list_periods(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> list[PayrollPeriodListItem]:
    return PayrollService(db).list_periods()


@router.post("/periods", response_model=PayrollWorkbookResponse, status_code=status.HTTP_201_CREATED)
def create_period(
    payload: CreatePayrollPeriodRequest,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).create_period(payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/periods/{period_id}/workbook", response_model=PayrollWorkbookResponse)
def get_workbook(
    period_id: int,
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).get_workbook(period_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/periods/{period_id}/recalculate", response_model=PayrollWorkbookResponse)
def recalculate_period(
    period_id: int,
    from_attendance: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).recalculate_period(period_id, user, from_attendance=from_attendance)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/periods/{period_id}/lines/{line_item_id}", response_model=PayrollWorkbookResponse)
def update_line(
    period_id: int,
    line_item_id: int,
    payload: UpdatePayrollLineRequest,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).update_line(period_id, line_item_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/periods/{period_id}/lines/{line_item_id}/payments", response_model=PayrollWorkbookResponse)
def record_payment(
    period_id: int,
    line_item_id: int,
    payload: RecordPayrollPaymentRequest,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).record_payment(period_id, line_item_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/periods/{period_id}/lines/{line_item_id}/mark-paid", response_model=PayrollWorkbookResponse)
def mark_worker_paid(
    period_id: int,
    line_item_id: int,
    payment_date: date | None = None,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).mark_worker_paid(period_id, line_item_id, user, payment_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/periods/{period_id}/mark-all-paid", response_model=PayrollWorkbookResponse)
def mark_all_paid(
    period_id: int,
    payment_date: date | None = None,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).mark_all_paid(period_id, user, payment_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/periods/{period_id}/finalize", response_model=PayrollWorkbookResponse)
def finalize_period(
    period_id: int,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("ADMIN")),
) -> PayrollWorkbookResponse:
    try:
        return PayrollService(db).finalize_period(period_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
