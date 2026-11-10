from fastapi import FastAPI

from app.config import APP_NAME, APP_VERSION
from app.routers.services import router as services_router
from app.routers.system import router as system_router

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

app.include_router(system_router)
app.include_router(services_router)
