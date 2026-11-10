import httpx

from app.config import settings


async def send_notification(
    recipient: str,
    message: str,
) -> dict:
    url = f"{settings.notification_service_url}/notifications"
    payload = {
        "recipient": recipient,
        "message": message,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()


async def get_notification(
    notification_id: int,
) -> dict:
    url = (
        f"{settings.notification_service_url}"
        f"/notifications/{notification_id}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
