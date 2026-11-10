import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault(
    "NOTIFICATION_SERVICE_URL",
    "http://127.0.0.1:9999",
)
os.environ.setdefault("NOTIFICATION_TIMEOUT_SECONDS", "0.5")
os.environ.setdefault("NOTIFICATION_MAX_ATTEMPTS", "3")
os.environ.setdefault("NOTIFICATION_RETRY_DELAY_SECONDS", "0.1")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from app.config import settings
from app.integrations.notification_client import (
    NotificationServiceUnavailable,
    send_notification,
)
from app.logging_config import configure_logging

configure_logging(settings.log_level)


async def main():
    print("Configured max attempts:", settings.notification_max_attempts)

    try:
        await send_notification(
            recipient="debug@cloud.local",
            message="LR32 debug",
        )
    except NotificationServiceUnavailable:
        print("EXPECTED_RESULT: service unavailable")


if __name__ == "__main__":
    asyncio.run(main())
