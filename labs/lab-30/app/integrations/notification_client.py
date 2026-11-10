import asyncio

import httpx

from app.config import settings


class NotificationServiceError(Exception):
    pass


class NotificationServiceUnavailable(NotificationServiceError):
    pass


class NotificationServiceTimeout(NotificationServiceError):
    pass


class NotificationServiceBadResponse(NotificationServiceError):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(
            f"Notification service returned HTTP {status_code}"
        )


async def send_notification(
    recipient: str,
    message: str,
) -> dict:
    url = f"{settings.notification_service_url}/notifications"
    payload = {
        "recipient": recipient,
        "message": message,
    }

    timeout = httpx.Timeout(settings.notification_timeout_seconds)
    max_attempts = settings.notification_max_attempts

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            if attempt == max_attempts:
                raise NotificationServiceUnavailable() from exc

            delay = (
                settings.notification_retry_delay_seconds
                * (2 ** (attempt - 1))
            )
            await asyncio.sleep(delay)
        except httpx.TimeoutException as exc:
            raise NotificationServiceTimeout() from exc
        except httpx.HTTPStatusError as exc:
            raise NotificationServiceBadResponse(
                exc.response.status_code
            ) from exc
        except httpx.RequestError as exc:
            raise NotificationServiceUnavailable() from exc

    raise NotificationServiceUnavailable()


async def get_notification(
    notification_id: int,
) -> dict:
    url = (
        f"{settings.notification_service_url}"
        f"/notifications/{notification_id}"
    )

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(settings.notification_timeout_seconds)
    ) as client:
        response = await client.get(url)
        return response.json()
