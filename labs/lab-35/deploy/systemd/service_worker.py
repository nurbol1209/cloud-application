import sys
import time
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

FAIL_FLAG = Path("/opt/cloud-lab/fail.flag")


if FAIL_FLAG.exists():
    print(
        "STARTUP ERROR: fail.flag detected",
        file=sys.stderr,
        flush=True,
    )
    raise SystemExit(42)


print(
    "cloud-lab-worker started",
    flush=True,
)


while True:
    timestamp = datetime.now(timezone.utc).isoformat()

    print(
        "heartbeat",
        timestamp,
        flush=True,
    )

    time.sleep(5)
