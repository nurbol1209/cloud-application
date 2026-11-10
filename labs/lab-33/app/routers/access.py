from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.schemas.access import (
    RoleAssign,
    RoleResponse,
    UserAccessResponse,
)
from app.security.authorization import (
    require_any_permission,
    require_permission,
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
def read_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.manage")),
):
    roles = get_roles(db)
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": sorted(permission.code for permission in role.permissions),
        }
        for role in roles
    ]


@router.get(
    "/users/{user_id}",
    response_model=UserAccessResponse,
    summary="Получить роль пользователя",
)
def read_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.manage")),
):
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
    current_user: User = Depends(require_permission("roles.manage")),
):
    user, error = assign_role(db, user_id, role_data.role_name)
    if error == "user":
        raise HTTPException(status_code=404, detail="User not found")
    if error == "role":
        raise HTTPException(status_code=404, detail="Role not found")
    return get_user_access(db, user.id)


@router.get(
    "/summary",
    summary="Сводка модели доступа",
)
def read_access_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_any_permission("users.manage", "roles.manage")
    ),
):
    roles = get_roles(db)
    return {
        "roles": [role.name for role in roles],
        "permissions": sorted(
            {permission.code for role in roles for permission in role.permissions}
        ),
        "requested_by": current_user.username,
    }
