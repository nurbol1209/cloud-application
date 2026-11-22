def build_service_report(
    services: list[dict],
    service_types: list[dict],
) -> list[dict]:
    types_by_id = {item["id"]: item["name"] for item in service_types}

    report = []
    for service in services:
        type_name = types_by_id.get(service["type_id"], "unknown")
        report.append(
            {
                "id": service["id"],
                "name": service["name"],
                "status": service["status"],
                "type": type_name,
            }
        )
    return report
