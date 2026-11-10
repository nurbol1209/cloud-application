from fastapi import APIRouter, HTTPException, Path

from app.schemas.services import ServiceCreate
from app.services.services import (
    create_service,
    delete_service,
    get_all_services,
    get_service_by_id,
    update_service,
)

router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "",
    summary="Получить список сервисов",
    description="Возвращает все сервисы, известные приложению.",
)
def read_services():
    return get_all_services()


@router.get(
    "/{service_id}",
    summary="Получить сервис по идентификатору",
    responses={404: {"description": "Сервис не найден"}},
)
def read_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    )
):
    service = get_service_by_id(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post(
    "",
    status_code=201,
    summary="Создать сервис",
    responses={422: {"description": "Некорректные входные данные"}},
)
def add_service(service: ServiceCreate):
    return create_service(service)


@router.put(
    "/{service_id}",
    summary="Изменить сервис",
    responses={404: {"description": "Сервис не найден"}},
)
def edit_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    ),
    service: ServiceCreate = ...,
):
    updated = update_service(service_id, service)
    if updated is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated


@router.delete(
    "/{service_id}",
    summary="Удалить сервис",
    responses={404: {"description": "Сервис не найден"}},
)
def remove_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    )
):
    deleted = delete_service(service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "message": "Service deleted",
        "id": service_id,
    }
