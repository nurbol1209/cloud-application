from fastapi import FastAPI, HTTPException, Path

from app.config import APP_NAME, APP_VERSION
from app.models import ServiceCreate

tags_metadata = [
    {
        "name": "System",
        "description": "Служебные маршруты приложения.",
    },
    {
        "name": "Services",
        "description": (
            "Операции с облачными сервисами: просмотр, создание, "
            "изменение и удаление."
        ),
    },
]

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Учебное облачное приложение для управления сервисами. "
        "Проект развивается в лабораторных работах по дисциплине "
        "«Управление работами и разработка программного обеспечения "
        "облачных систем»."
    ),
    openapi_tags=tags_metadata,
)

services = [
    {
        "id": 1,
        "name": "Web Service",
        "type": "application",
        "status": "running",
    },
    {
        "id": 2,
        "name": "Database Service",
        "type": "database",
        "status": "running",
    },
]


@app.get("/", tags=["System"], summary="Сведения о приложении")
def root():
    """Возвращает название, версию и состояние приложения."""
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ok",
    }


@app.get("/status", tags=["System"], summary="Состояние приложения")
def status():
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@app.get("/about", tags=["System"], summary="Описание проекта")
def about():
    return {
        "name": APP_NAME,
        "type": "cloud application",
        "language": "Python",
        "framework": "FastAPI",
    }


@app.get("/course", tags=["System"], summary="Сведения о дисциплине")
def course():
    return {
        "discipline": (
            "Управление работами и разработка программного обеспечения "
            "облачных систем"
        ),
        "laboratory": 6,
        "project": APP_NAME,
    }


@app.get(
    "/services",
    tags=["Services"],
    summary="Получить список сервисов",
    description="Возвращает все сервисы, известные приложению.",
)
def get_services():
    return services


@app.get(
    "/services/{service_id}",
    tags=["Services"],
    summary="Получить сервис по идентификатору",
    description="Возвращает один сервис или ошибку 404, если он не найден.",
    responses={404: {"description": "Сервис не найден"}},
)
def get_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    )
):
    for service in services:
        if service["id"] == service_id:
            return service
    raise HTTPException(status_code=404, detail="Service not found")


@app.post(
    "/services",
    tags=["Services"],
    status_code=201,
    summary="Создать сервис",
    description="Создаёт новый сервис и возвращает его с присвоенным id.",
    responses={422: {"description": "Некорректные входные данные"}},
)
def create_service(service: ServiceCreate):
    new_id = max((item["id"] for item in services), default=0) + 1
    new_service = {
        "id": new_id,
        "name": service.name,
        "type": service.type,
        "status": service.status,
    }
    services.append(new_service)
    return new_service


@app.put(
    "/services/{service_id}",
    tags=["Services"],
    summary="Изменить сервис",
    description="Полностью заменяет данные существующего сервиса.",
    responses={404: {"description": "Сервис не найден"}},
)
def update_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    ),
    service: ServiceCreate = ...,
):
    for item in services:
        if item["id"] == service_id:
            item["name"] = service.name
            item["type"] = service.type
            item["status"] = service.status
            return item
    raise HTTPException(status_code=404, detail="Service not found")


@app.delete(
    "/services/{service_id}",
    tags=["Services"],
    summary="Удалить сервис",
    description="Удаляет сервис по идентификатору.",
    responses={404: {"description": "Сервис не найден"}},
)
def delete_service(
    service_id: int = Path(
        ...,
        description="Уникальный идентификатор сервиса",
        gt=0,
    )
):
    for item in services:
        if item["id"] == service_id:
            services.remove(item)
            return {
                "message": "Service deleted",
                "id": service_id,
            }
    raise HTTPException(status_code=404, detail="Service not found")
