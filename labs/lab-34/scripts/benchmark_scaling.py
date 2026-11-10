import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.reporting import build_service_report
from scripts.profile_service_report import create_dataset


def build_service_report_linear(
    services: list[dict],
    service_types: list[dict],
) -> list[dict]:
    report = []
    for service in services:
        type_name = "unknown"
        for service_type in service_types:
            if service_type["id"] == service["type_id"]:
                type_name = service_type["name"]
                break
        report.append(
            {
                "id": service["id"],
                "name": service["name"],
                "status": service["status"],
                "type": type_name,
            }
        )
    return report


def measure(
    build,
    services: list[dict],
    service_types: list[dict],
    repeats: int = 5,
) -> float:
    times = []
    for _ in range(repeats):
        started = time.perf_counter()
        build(services, service_types)
        times.append(time.perf_counter() - started)
    return statistics.mean(times)


def main() -> None:
    print("service_count  linear_mean  dict_mean  speedup")

    for service_count in (5_000, 20_000, 50_000):
        services, service_types = create_dataset(service_count, 200)
        linear = measure(build_service_report_linear, services, service_types)
        by_dict = measure(build_service_report, services, service_types)
        print(
            f"{service_count:>12}  {linear:.6f}  {by_dict:.6f}  {linear / by_dict:.2f}"
        )

    print()
    print("type_count  linear_mean  dict_mean  speedup")

    for type_count in (20, 200, 1_000):
        services, service_types = create_dataset(20_000, type_count)
        linear = measure(build_service_report_linear, services, service_types)
        by_dict = measure(build_service_report, services, service_types)
        print(f"{type_count:>10}  {linear:.6f}  {by_dict:.6f}  {linear / by_dict:.2f}")


if __name__ == "__main__":
    main()
