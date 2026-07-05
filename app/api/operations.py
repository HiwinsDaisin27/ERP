from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.auth import WebUser
from app.models.construction import Attendance, Employee, Site
from app.models.payroll import PayrollLineItem, PayrollPeriod
from app.schemas.operations import (
    AttendanceHistoryItem,
    PayrollHistoryItem,
    SiteCreateRequest,
    SiteResponse,
    WorkerCreateRequest,
    WorkerProfileResponse,
    WorkerResponse,
)

router = APIRouter(prefix="/operations", tags=["operations"])


def _site_response(site: Site) -> SiteResponse:
    return SiteResponse(
        site_id=site.site_id,
        site_name=site.site_name,
        location=site.location,
        supervisor_name=site.supervisor_name,
        project_start_date=site.project_start_date,
        expected_end_date=site.expected_end_date,
        project_budget=site.project_budget,
        status=site.status,
    )


def _worker_response(worker: Employee) -> WorkerResponse:
    return WorkerResponse(
        employee_id=worker.employee_id,
        full_name=worker.full_name,
        phone_number=worker.phone_number,
        role=worker.role,
        wage_type=worker.wage_type,
        daily_rate=worker.daily_rate,
        weekly_rate=worker.weekly_rate,
        joining_date=worker.joining_date,
        image_url=worker.image_url,
        status=worker.status,
    )


@router.get("/sites", response_model=list[SiteResponse])
def list_sites(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> list[SiteResponse]:
    sites = db.scalars(select(Site).order_by(Site.site_name)).all()
    return [_site_response(site) for site in sites]


@router.post("/sites", response_model=SiteResponse)
def create_site(
    payload: SiteCreateRequest,
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("ADMIN")),
) -> SiteResponse:
    existing = db.scalar(select(Site).where(func.lower(Site.site_name) == payload.site_name.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A site with this name already exists")

    site = Site(**payload.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return _site_response(site)


@router.get("/workers", response_model=list[WorkerResponse])
def list_workers(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> list[WorkerResponse]:
    workers = db.scalars(select(Employee).order_by(Employee.full_name)).all()
    return [_worker_response(worker) for worker in workers]


@router.post("/workers", response_model=WorkerResponse)
def create_worker(
    payload: WorkerCreateRequest,
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("ADMIN")),
) -> WorkerResponse:
    if payload.phone_number:
        existing_phone = db.scalar(select(Employee).where(Employee.phone_number == payload.phone_number))
        if existing_phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A worker with this phone already exists")

    worker = Employee(**payload.model_dump())
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return _worker_response(worker)


@router.get("/workers/{employee_id}", response_model=WorkerProfileResponse)
def worker_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> WorkerProfileResponse:
    worker = db.get(Employee, employee_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    attendance_rows = db.execute(
        select(Attendance, Site.site_name)
        .join(Site, Site.site_id == Attendance.site_id)
        .where(Attendance.employee_id == employee_id)
        .order_by(Attendance.attendance_date.desc(), Attendance.attendance_id.desc())
        .limit(120)
    ).all()
    payroll_rows = db.execute(
        select(PayrollLineItem, PayrollPeriod)
        .join(PayrollPeriod, PayrollPeriod.period_id == PayrollLineItem.period_id)
        .where(PayrollLineItem.employee_id == employee_id)
        .order_by(PayrollPeriod.period_start.desc(), PayrollLineItem.line_item_id.desc())
        .limit(60)
    ).all()

    return WorkerProfileResponse(
        worker=_worker_response(worker),
        attendance=[
            AttendanceHistoryItem(
                attendance_id=row.attendance_id,
                site_id=row.site_id,
                site_name=site_name,
                attendance_date=row.attendance_date,
                attendance_status=row.attendance_status,
                overtime_hours=row.overtime_hours,
                remarks=row.remarks,
            )
            for row, site_name in attendance_rows
        ],
        payroll=[
            PayrollHistoryItem(
                period_id=period.period_id,
                period_start=period.period_start,
                period_end=period.period_end,
                status=period.status,
                gross_wage=line.gross_wage,
                amount_paid=line.amount_paid,
                balance_due=line.balance_due,
            )
            for line, period in payroll_rows
        ],
    )
