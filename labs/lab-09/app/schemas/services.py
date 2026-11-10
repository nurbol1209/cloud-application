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
    status: str = Field(
        ...,
        description="Текущее состояние сервиса",
        examples=["running"],
    )
