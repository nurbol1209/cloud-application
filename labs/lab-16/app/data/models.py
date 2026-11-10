from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


class ServiceType(Base):
    __tablename__ = "service_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    services: Mapped[list["Service"]] = relationship(
        back_populates="service_type",
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id"))
    status: Mapped[str] = mapped_column(String(20))
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
