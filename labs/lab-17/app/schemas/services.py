from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ServiceStatus = Literal["running", "maintenance", "stopped"]


class ServiceCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Название облачного сервиса",
        examples=["Monitoring Service"],
    )
    type: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Тип облачного сервиса",
        examples=["monitoring"],
    )
    status: ServiceStatus = Field(
        ...,
        description="Текущее состояние сервиса",
        examples=["running"],
    )

    @field_validator("name", "type", mode="before")
    @classmethod
    def strip_text(cls, value: Any):
        if isinstance(value, str):
            return value.strip()
        return value


class ServiceEndpointUpdate(BaseModel):
    endpoint_url: str = Field(
        ...,
        min_length=8,
        max_length=255,
    )

    @field_validator("endpoint_url", mode="before")
    @classmethod
    def strip_endpoint_url(cls, value: Any):
        if isinstance(value, str):
            return value.strip()
        return value
