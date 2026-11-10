from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.schemas.access import (
    RoleAssign,
    RoleResponse,
    UserAccessResponse,
)
from app.services.access import assign_role, get_roles, get_user_access

router = APIRouter(
    prefix="/access",
    tags=["Access Model"],
)


@router.get(
    "/roles",
    response_model=list[RoleResponse],
    summary="Получить роли и разрешения",
)
def read_roles(db: Session = Depends(get_db)):
    roles = get_roles(db)
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": sorted(
                permission.code for permission in role.permissions
            ),
        }
        for role in roles
    ]


@router.get(
    "/users/{user_id}",
    response_model=UserAccessResponse,
    summary="Получить роль пользователя",
)
def read_user_access(user_id: int, db: Session = Depends(get_db)):
    result = get_user_access(db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.put(
    "/users/{user_id}/role",
    response_model=UserAccessResponse,
    summary="Назначить роль пользователю",
)
def update_user_role(
    user_id: int,
    role_data: RoleAssign,
    db: Session = Depends(get_db),
):
    user, error = assign_role(db, user_id, role_data.role_name)
    if error == "user":
        raise HTTPException(status_code=404, detail="User not found")
    if error == "role":
        raise HTTPException(status_code=404, detail="Role not found")
    return get_user_access(db, user.id)
