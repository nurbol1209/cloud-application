from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


class ServiceType(Base):
    __tablename__ = "service_types"
    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_service_types_name",
        ),
        CheckConstraint(
            "TRIM(name) <> ''",
            name="ck_service_types_name_not_empty",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="service_type",
    )


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'maintenance', 'stopped')",
            name="ck_services_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("service_types.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    endpoint_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    service_type: Mapped["ServiceType"] = relationship(
        back_populates="services",
    )
