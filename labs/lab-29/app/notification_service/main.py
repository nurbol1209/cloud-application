from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Notification Service",
    version="1.0.0",
)


class NotificationCreate(BaseModel):
    recipient: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Адрес получателя уведомления",
        examples=["operator@cloud.local"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст уведомления",
        examples=["Cloud Application is running"],
    )


class NotificationResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: Literal["accepted"]


notifications: list[dict] = []


@app.get(
    "/status",
    summary="Проверить состояние сервиса",
)
def status():
    return {
        "service": "notification",
        "status": "running",
    }


@app.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=201,
    summary="Принять уведомление",
)
def create_notification(
    notification: NotificationCreate,
):
    item = {
        "id": len(notifications) + 1,
        "recipient": notification.recipient,
        "message": notification.message,
        "status": "accepted",
    }
    notifications.append(item)
    return item


@app.get(
    "/notifications",
    response_model=list[NotificationResponse],
    summary="Получить принятые уведомления",
)
def get_notifications():
    return notifications


@app.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
    summary="Получить уведомление по идентификатору",
)
def get_notification(notification_id: int):
    for item in notifications:
        if item["id"] == notification_id:
            return item
    raise HTTPException(
        status_code=404,
        detail="Notification not found",
    )
