from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    type: str
    status: str
