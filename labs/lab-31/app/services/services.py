from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Service, ServiceType
from app.schemas.services import ServiceCreate


def service_to_dict(service: Service):
    return {
        "id": service.id,
        "name": service.name,
        "type": service.service_type.name,
        "status": service.status,
    }


def get_all_services(db: Session):
    statement = select(Service).order_by(Service.id)
    return db.scalars(statement).all()


def get_service_by_id(db: Session, service_id: int):
    return db.get(Service, service_id)


def get_service_type(db: Session, type_name: str):
    statement = select(ServiceType).where(ServiceType.name == type_name)
    return db.scalar(statement)


def get_services_by_status(db: Session, status: str):
    statement = (
        select(Service)
        .where(Service.status == status)
        .order_by(Service.id)
    )
    return db.scalars(statement).all()


def create_service(db: Session, service_data: ServiceCreate):
    service_type = get_service_type(db, service_data.type)
    if service_type is None:
        return None
    service = Service(
        name=service_data.name,
        type_id=service_type.id,
        status=service_data.status,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def update_service(
    db: Session,
    service_id: int,
    service_data: ServiceCreate,
):
    service = get_service_by_id(db, service_id)
    if service is None:
        return None, "service"
    service_type = get_service_type(db, service_data.type)
    if service_type is None:
        return None, "type"
    service.name = service_data.name
    service.type_id = service_type.id
    service.status = service_data.status
    db.commit()
    db.refresh(service)
    return service, None


def delete_service(db: Session, service: Service):
    db.delete(service)
    db.commit()


def count_services(db: Session):
    return len(get_all_services(db))
