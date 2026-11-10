from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


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


class StoredObject(Base):
    __tablename__ = "stored_objects"
    __table_args__ = (
        UniqueConstraint(
            "storage_name",
            name="uq_stored_objects_storage_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "username",
            name="uq_users_username",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # Учебное хранение: в ЛР №22 будет заменено хешем пароля.
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    role: Mapped["Role | None"] = relationship(
        back_populates="users",
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint(
            "token",
            name="uq_auth_sessions_token",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="sessions",
    )


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_permissions_code",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_roles_name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
    )
    users: Mapped[list["User"]] = relationship(
        back_populates="role",
    )
