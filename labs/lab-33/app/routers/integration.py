from fastapi import APIRouter, Depends, HTTPException

from app.data.models import User
from app.integrations.notification_client import (
    NotificationServiceBadResponse,
    NotificationServiceTimeout,
    NotificationServiceUnavailable,
    send_notification,
)
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
    status_code=201,
    summary="Передать уведомление внутреннему сервису",
)
async def forward_notification(
    notification: NotificationSendRequest,
    current_user: User = Depends(require_permission("services.write")),
):
    try:
        result = await send_notification(
            recipient=notification.recipient,
            message=notification.message,
        )
        return result
    except NotificationServiceTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Notification service response timeout",
        ) from exc
    except NotificationServiceUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Notification service is unavailable",
        ) from exc
    except NotificationServiceBadResponse as exc:
        raise HTTPException(
            status_code=502,
            detail="Notification service returned an invalid response",
        ) from exc
