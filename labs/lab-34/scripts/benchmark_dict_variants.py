import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.reporting import build_service_report
from scripts.profile_service_report import create_dataset


def build_by_item(services: list[dict], service_types: list[dict]) -> list[dict]:
    types_by_id = {item["id"]: item for item in service_types}
    report = []
    for service in services:
        type_name = types_by_id[service["type_id"]]["name"]
        report.append(
            {
                "id": service["id"],
                "name": service["name"],
                "status": service["status"],
                "type": type_name,
            }
        )
    return report


def measure(build, services: list[dict], service_types: list[dict]) -> list[float]:
    times = []
    for _ in range(7):
        started = time.perf_counter()
        build(services, service_types)
        times.append(time.perf_counter() - started)
    return times


def main() -> None:
    services, service_types = create_dataset(20_000, 200)

    by_name = measure(build_service_report, services, service_types)
    by_item = measure(build_by_item, services, service_types)

    print("variant     mean       best       min-max")
    print(
        f"id->name    {statistics.mean(by_name):.6f}  "
        f"{min(by_name):.6f}  "
        f"{min(by_name):.6f}-{max(by_name):.6f}"
    )
    print(
        f"id->item    {statistics.mean(by_item):.6f}  "
        f"{min(by_item):.6f}  "
        f"{min(by_item):.6f}-{max(by_item):.6f}"
    )
    print(
        f"means differ by {abs(statistics.mean(by_name) - statistics.mean(by_item)):.6f}s"
    )


if __name__ == "__main__":
    main()
