from fastapi import APIRouter

from app.config import APP_NAME, APP_VERSION
from app.services.services import count_services

router = APIRouter(tags=["System"])


@router.get("/", summary="Сведения о приложении")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ok",
    }


@router.get("/status", summary="Состояние приложения")
def status():
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@router.get("/about", summary="Описание проекта")
def about():
    return {
        "name": APP_NAME,
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
        "laboratory": 7,
        "project": APP_NAME,
    }


@router.get("/service-count", summary="Количество сервисов")
def service_count():
    return {"count": count_services()}
