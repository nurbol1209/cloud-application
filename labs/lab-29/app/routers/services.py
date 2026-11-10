from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.schemas.services import ServiceCreate, ServiceStatus
from app.security.authorization import require_permission
from app.services.services import (
    create_service,
    delete_service,
    get_all_services,
    get_service_by_id,
    get_services_by_status,
    service_to_dict,
    update_service,
)

router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "",
    summary="Получить список сервисов",
    description=(
        "Возвращает все сервисы или только сервисы с указанным состоянием."
    ),
)
def read_services(
    status: ServiceStatus | None = Query(
        default=None,
        description="Фильтр по состоянию сервиса",
        examples=["running"],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("services.read")
    ),
):
    if status is None:
        services = get_all_services(db)
    else:
        services = get_services_by_status(db, status)
    return [service_to_dict(service) for service in services]


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
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("services.read")
    ),
):
    service = get_service_by_id(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service_to_dict(service)


@router.post(
    "",
    status_code=201,
    summary="Создать сервис",
    responses={
        400: {"description": "Тип сервиса не найден"},
        422: {"description": "Некорректные входные данные"},
    },
)
def add_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    created = create_service(db, service)
    if created is None:
        raise HTTPException(status_code=400, detail="Service type not found")
    return service_to_dict(created)


@router.put(
    "/{service_id}",
    summary="Изменить сервис",
    responses={
        400: {"description": "Тип сервиса не найден"},
        404: {"description": "Сервис не найден"},
    },
)
def edit_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    ),
    service: ServiceCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    updated, error = update_service(db, service_id, service)
    if error == "service":
        raise HTTPException(status_code=404, detail="Service not found")
    if error == "type":
        raise HTTPException(status_code=400, detail="Service type not found")
    return service_to_dict(updated)


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
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    service = get_service_by_id(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    delete_service(db, service)
    return {
        "message": "Service deleted",
        "id": service_id,
    }
