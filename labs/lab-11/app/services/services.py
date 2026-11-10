from app.data.services import services_data
from app.schemas.services import ServiceCreate


def get_all_services():
    return services_data


def get_services_by_status(status: str):
    return [
        service
        for service in services_data
        if service["status"] == status
    ]


def get_service_by_id(service_id: int):
    for service in services_data:
        if service["id"] == service_id:
            return service
    return None


def create_service(service_data: ServiceCreate):
    new_id = max(
        (item["id"] for item in services_data),
        default=0,
    ) + 1
    new_service = {
        "id": new_id,
        "name": service_data.name,
        "type": service_data.type,
        "status": service_data.status,
    }
    services_data.append(new_service)
    return new_service


def update_service(service_id: int, service_data: ServiceCreate):
    service = get_service_by_id(service_id)
    if service is None:
        return None
    service["name"] = service_data.name
    service["type"] = service_data.type
    service["status"] = service_data.status
    return service


def delete_service(service_id: int):
    service = get_service_by_id(service_id)
    if service is None:
        return False
    services_data.remove(service)
    return True


def count_services():
    return len(services_data)
