import json
import logging
import logging.config
import sys
from datetime import datetime, timezone

from app.request_context import get_request_id

EXTRA_FIELDS = (
    "service",
    "event",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "user_id",
    "username",
    "permission",
    "target_service",
    "attempt",
    "error_type",
    "notification_id",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }

        for field in EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level.upper(),
            "handlers": ["console"],
        },
    }
    logging.config.dictConfig(logging_config)
