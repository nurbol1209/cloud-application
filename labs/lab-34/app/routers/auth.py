from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SessionResponse,
    UserRegister,
    UserResponse,
)
from app.security.authorization import get_current_user
from app.services.auth import (
    authenticate_user,
    get_auth_session,
    logout_all_sessions,
    logout_user,
    register_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Зарегистрировать пользователя",
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    user = register_user(db, user_data)
    if user is None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )
    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Выполнить вход",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    session = authenticate_user(db, login_data)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    return {
        "access_token": session.token,
        "token_type": "session",
    }


@router.get(
    "/me",
    summary="Получить текущего пользователя",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": (current_user.role.name if current_user.role else None),
    }


@router.get(
    "/session/{token}",
    response_model=SessionResponse,
    summary="Проверить сеанс",
)
def check_session(
    token: str,
    db: Session = Depends(get_db),
):
    session = get_auth_session(db, token)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )
    return {
        "authenticated": True,
        "user_id": session.user.id,
        "username": session.user.username,
    }


@router.delete(
    "/session/{token}",
    summary="Завершить сеанс",
)
def logout(
    token: str,
    db: Session = Depends(get_db),
):
    result = logout_user(db, token)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )
    return {"message": "Session closed"}


@router.delete(
    "/user/{user_id}/sessions",
    summary="Завершить все сеансы пользователя",
)
def logout_all(
    user_id: int,
    db: Session = Depends(get_db),
):
    closed_sessions = logout_all_sessions(db, user_id)
    return {
        "message": "Sessions closed",
        "user_id": user_id,
        "closed_sessions": closed_sessions,
    }
