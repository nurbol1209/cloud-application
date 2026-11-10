import logging
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.data.models import AuthSession, Role, User
from app.schemas.auth import LoginRequest, UserRegister
from app.security.passwords import hash_password, verify_password

logger = logging.getLogger(__name__)


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def register_user(db: Session, user_data: UserRegister) -> User | None:
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user is not None:
        return None

    default_role = db.scalar(
        select(Role).where(Role.name == "viewer")
    )

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role_id=default_role.id if default_role else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    login_data: LoginRequest,
) -> AuthSession | None:
    user = get_user_by_username(db, login_data.username)
    if user is None:
        logger.warning(
            "Authentication failed",
            extra={
                "service": "cloud-application",
                "event": "authentication_failed",
                "username": login_data.username,
            },
        )
        return None
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(
            "Authentication failed",
            extra={
                "service": "cloud-application",
                "event": "authentication_failed",
                "username": login_data.username,
            },
        )
        return None

    session = AuthSession(
        token=uuid4().hex,
        user_id=user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(
        "Authentication succeeded",
        extra={
            "service": "cloud-application",
            "event": "authentication_succeeded",
            "user_id": user.id,
            "username": user.username,
        },
    )

    return session


def get_auth_session(db: Session, token: str) -> AuthSession | None:
    statement = select(AuthSession).where(AuthSession.token == token)
    return db.scalar(statement)


def logout_user(db: Session, token: str) -> bool:
    session = get_auth_session(db, token)
    if session is None:
        return False

    db.delete(session)
    db.commit()
    return True


def logout_all_sessions(db: Session, user_id: int) -> int:
    result = db.execute(
        delete(AuthSession).where(AuthSession.user_id == user_id)
    )
    db.commit()
    return result.rowcount or 0
