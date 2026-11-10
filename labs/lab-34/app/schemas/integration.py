from pydantic import BaseModel, Field


class NotificationSendRequest(BaseModel):
    recipient: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Адрес получателя уведомления",
        examples=["operator@cloud.local"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Текст уведомления",
        examples=["Cloud Application is running"],
    )


class NotificationSendResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: str
