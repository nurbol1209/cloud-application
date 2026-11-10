from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.services.auth import get_auth_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session = get_auth_session(db, credentials.credentials)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session.user


def require_permission(permission_code: str):
    def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role is None:
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        user_permissions = {
            permission.code
            for permission in current_user.role.permissions
        }
        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: {permission_code}",
            )
        return current_user

    return permission_dependency


def require_any_permission(*permission_codes: str):
    def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role is None:
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        user_permissions = {
            permission.code
            for permission in current_user.role.permissions
        }
        if not user_permissions.intersection(permission_codes):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Insufficient permissions: "
                    + ", ".join(permission_codes)
                ),
            )
        return current_user

    return permission_dependency
