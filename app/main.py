from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.api.payroll import router as payroll_router
from app.api.root import router as root_router
from app.api.telegram_webhook import router as telegram_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(root_router)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(assistant_router)
    app.include_router(dashboard_router)
    app.include_router(operations_router)
    app.include_router(payroll_router)
    app.include_router(telegram_router)
    return app


app = create_app()
