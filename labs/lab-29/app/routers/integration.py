from fastapi import APIRouter, Depends

from app.data.models import User
from app.integrations.notification_client import send_notification
from app.schemas.integration import (
    NotificationSendRequest,
    NotificationSendResponse,
)
from app.security.authorization import require_permission

router = APIRouter(
    prefix="/integration",
    tags=["Integration"],
)


@router.post(
    "/notifications",
    response_model=NotificationSendResponse,
    summary="Передать уведомление внутреннему сервису",
)
async def forward_notification(
    notification: NotificationSendRequest,
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    result = await send_notification(
        recipient=notification.recipient,
        message=notification.message,
    )
    return result
