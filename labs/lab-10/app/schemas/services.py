from typing import Literal

from pydantic import BaseModel, Field


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
    status: Literal["running", "maintenance", "stopped"] = Field(
        ...,
        description="Текущее состояние сервиса",
        examples=["running"],
    )
