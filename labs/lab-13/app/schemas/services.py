from typing import Literal

from pydantic import BaseModel, Field

ServiceStatus = Literal["running", "maintenance", "stopped"]


class ServiceCreate(BaseModel):
    name: str = Field(
        ...,
        description="Название облачного сервиса",
        examples=["Monitoring Service"],
    )
    type: str = Field(
        ...,
        description="Тип облачного сервиса",
        examples=["monitoring"],
    )
    status: ServiceStatus = Field(
        ...,
        description="Текущее состояние сервиса",
        examples=["running"],
    )
