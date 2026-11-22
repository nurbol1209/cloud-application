import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.reporting import build_service_report  # noqa: E402

SERVICE_COUNT = 20_000
TYPE_COUNT = 200
REPEATS = 5


def create_dataset(
    service_count: int = SERVICE_COUNT,
    type_count: int = TYPE_COUNT,
) -> tuple[list[dict], list[dict]]:
    service_types = [
        {
            "id": type_id,
            "name": f"type-{type_id}",
        }
        for type_id in range(1, type_count + 1)
    ]

    statuses = (
        "running",
        "maintenance",
        "stopped",
    )

    services = [
        {
            "id": service_id,
            "name": f"service-{service_id}",
            "type_id": ((service_id * 37) % type_count) + 1,
            "status": statuses[service_id % len(statuses)],
        }
        for service_id in range(1, service_count + 1)
    ]

    return services, service_types


def result_digest(report: list[dict]) -> str:
    payload = json.dumps(
        report,
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark of the service report component.",
    )
    parser.add_argument("--services", type=int, default=SERVICE_COUNT)
    parser.add_argument("--types", type=int, default=TYPE_COUNT)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()

    services, service_types = create_dataset(
        args.services,
        args.types,
    )

    print(
        f"services={args.services} types={args.types} repeats={args.repeats}",
    )

    times = []
    last_report = None

    for run_number in range(1, args.repeats + 1):
        started = time.perf_counter()
        report = build_service_report(
            services,
            service_types,
        )
        elapsed = time.perf_counter() - started

        times.append(elapsed)
        last_report = report
        print(f"run={run_number} time={elapsed:.6f}s")

    print("records:", len(last_report))
    print("digest:", result_digest(last_report))
    print("mean:", f"{statistics.mean(times):.6f}s")
    print("best:", f"{min(times):.6f}s")


if __name__ == "__main__":
    main()
