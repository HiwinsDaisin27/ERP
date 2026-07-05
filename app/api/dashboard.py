from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.auth import WebUser
from app.schemas.dashboard import (
    AlertResponse,
    ChartSeriesResponse,
    DashboardOverviewResponse,
    InventoryRowResponse,
    SiteCardResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> DashboardOverviewResponse:
    return DashboardService(db).overview()


@router.get("/sites", response_model=list[SiteCardResponse])
def dashboard_sites(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> list[SiteCardResponse]:
    return DashboardService(db).site_cards()


@router.get("/attendance", response_model=ChartSeriesResponse)
def dashboard_attendance(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> ChartSeriesResponse:
    return DashboardService(db).attendance_chart(days=days)


@router.get("/inventory", response_model=list[InventoryRowResponse])
def dashboard_inventory(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> list[InventoryRowResponse]:
    return DashboardService(db).inventory_matrix()


@router.get("/budget", response_model=ChartSeriesResponse)
def dashboard_budget(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> ChartSeriesResponse:
    return DashboardService(db).budget_chart()


@router.get("/material-consumption", response_model=ChartSeriesResponse)
def dashboard_material_consumption(
    days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> ChartSeriesResponse:
    return DashboardService(db).material_consumption_trend(days=days)


@router.get("/alerts", response_model=list[AlertResponse])
def dashboard_alerts(
    db: Session = Depends(get_db),
    _: WebUser = Depends(require_roles("OPERATIONS", "MANAGEMENT", "ADMIN")),
) -> list[AlertResponse]:
    return DashboardService(db).alerts()
