from fastapi import FastAPI, HTTPException

from app.config import APP_NAME, APP_VERSION
from app.models import ServiceCreate

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
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


@app.get("/", summary="Сведения о приложении")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ok",
    }


@app.get("/status", summary="Состояние приложения")
def status():
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@app.get("/about", summary="Описание проекта")
def about():
    return {
        "name": APP_NAME,
        "type": "cloud application",
        "language": "Python",
        "framework": "FastAPI",
    }


@app.get("/course", summary="Сведения о дисциплине")
def course():
    return {
        "discipline": (
            "Управление работами и разработка программного обеспечения "
            "облачных систем"
        ),
        "laboratory": 5,
        "project": APP_NAME,
    }


@app.get("/services", summary="Получить список сервисов")
def get_services():
    return services


@app.get("/services/{service_id}", summary="Получить сервис по идентификатору")
def get_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            return service
    raise HTTPException(status_code=404, detail="Service not found")


@app.post("/services", status_code=201, summary="Создать сервис")
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


@app.put("/services/{service_id}", summary="Изменить сервис")
def update_service(service_id: int, service: ServiceCreate):
    for item in services:
        if item["id"] == service_id:
            item["name"] = service.name
            item["type"] = service.type
            item["status"] = service.status
            return item
    raise HTTPException(status_code=404, detail="Service not found")


@app.delete("/services/{service_id}", summary="Удалить сервис")
def delete_service(service_id: int):
    for item in services:
        if item["id"] == service_id:
            services.remove(item)
            return {
                "message": "Service deleted",
                "id": service_id,
            }
    raise HTTPException(status_code=404, detail="Service not found")
