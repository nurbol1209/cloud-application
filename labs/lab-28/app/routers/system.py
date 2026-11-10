from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.data.database import get_db
from app.services.services import count_services

router = APIRouter(tags=["System"])


@router.get("/", summary="Сведения о приложении")
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }


@router.get("/status", summary="Состояние приложения")
def status():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "debug": settings.debug,
        "api_prefix": settings.api_prefix,
    }


@router.get("/about", summary="Описание проекта")
def about():
    return {
        "name": settings.app_name,
        "type": "cloud application",
        "language": "Python",
        "framework": "FastAPI",
    }


@router.get("/course", summary="Сведения о дисциплине")
def course():
    return {
        "discipline": (
            "Управление работами и разработка программного обеспечения "
            "облачных систем"
        ),
        "laboratory": 23,
        "project": settings.app_name,
    }


@router.get("/service-count", summary="Количество сервисов")
def service_count(db: Session = Depends(get_db)):
    return {"count": count_services(db)}


@router.get("/connection", summary="Информация о соединении")
def connection_info(request: Request):
    return {
        "scheme": request.url.scheme,
        "host": request.url.hostname,
        "secure": request.url.scheme == "https",
    }
