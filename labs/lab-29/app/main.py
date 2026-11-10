from fastapi import FastAPI

from app.config import settings
from app.routers.access import router as access_router
from app.routers.auth import router as auth_router
from app.routers.integration import router as integration_router
from app.routers.objects import router as objects_router
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
    {
        "name": "Objects",
        "description": (
            "Файловое хранилище: загрузка, метаданные, скачивание "
            "и удаление объектов."
        ),
    },
    {
        "name": "Authentication",
        "description": (
            "Регистрация пользователей, вход, проверка и завершение "
            "сеансов."
        ),
    },
    {
        "name": "Access Model",
        "description": (
            "Роли и разрешения: матрица доступа, роль пользователя "
            "и её изменение."
        ),
    },
    {
        "name": "Integration",
        "description": (
            "Межсервисное взаимодействие: передача уведомлений "
            "внутреннему Notification Service по HTTP."
        ),
    },
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    openapi_tags=tags_metadata,
    debug=settings.debug,
)

app.include_router(system_router)
app.include_router(services_router)
app.include_router(objects_router)
app.include_router(auth_router)
app.include_router(access_router)
app.include_router(integration_router)
