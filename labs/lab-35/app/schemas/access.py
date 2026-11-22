from pydantic import BaseModel, Field


class RoleAssign(BaseModel):
    role_name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        examples=["operator"],
    )


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: list[str]


class UserAccessResponse(BaseModel):
    user_id: int
    username: str
    role: str | None
    permissions: list[str]
