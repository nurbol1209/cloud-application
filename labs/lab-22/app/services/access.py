from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Permission, Role, User

PERMISSIONS = {
    "services.read": "Просмотр сервисов",
    "services.write": "Изменение сервисов",
    "objects.read": "Просмотр и скачивание объектов",
    "objects.write": "Загрузка и удаление объектов",
    "users.manage": "Управление пользователями",
    "roles.manage": "Управление ролями",
}

ROLE_MODEL = {
    "viewer": {
        "description": "Просмотр данных",
        "permissions": [
            "services.read",
            "objects.read",
        ],
    },
    "operator": {
        "description": "Работа с сервисами и объектами",
        "permissions": [
            "services.read",
            "services.write",
            "objects.read",
            "objects.write",
        ],
    },
    "administrator": {
        "description": "Полное управление приложением",
        "permissions": [
            "services.read",
            "services.write",
            "objects.read",
            "objects.write",
            "users.manage",
            "roles.manage",
        ],
    },
    # Дополнительное задание: роль добавляется как данные, без миграции.
    "content_manager": {
        "description": "Управление файлами и объектами",
        "permissions": [
            "objects.read",
            "objects.write",
            "services.read",
        ],
    },
}


def initialize_access_model(db: Session) -> None:
    permissions = {}
    for code, description in PERMISSIONS.items():
        permission = db.scalar(
            select(Permission).where(Permission.code == code)
        )
        if permission is None:
            permission = Permission(code=code, description=description)
            db.add(permission)
            db.flush()
        permissions[code] = permission

    for role_name, role_data in ROLE_MODEL.items():
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )
        if role is None:
            role = Role(
                name=role_name,
                description=role_data["description"],
            )
            db.add(role)
            db.flush()
        role.permissions = [
            permissions[code] for code in role_data["permissions"]
        ]

    db.commit()


def assign_default_roles(db: Session) -> None:
    viewer = db.scalar(select(Role).where(Role.name == "viewer"))
    if viewer is None:
        return

    users = db.scalars(
        select(User).where(User.role_id.is_(None))
    ).all()
    for user in users:
        user.role_id = viewer.id
    db.commit()


def get_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.id)).all())


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == role_name))


def assign_role(
    db: Session,
    user_id: int,
    role_name: str,
) -> tuple[User | None, str | None]:
    user = db.get(User, user_id)
    if user is None:
        return None, "user"

    role = get_role_by_name(db, role_name)
    if role is None:
        return None, "role"

    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user, None


def get_user_access(db: Session, user_id: int) -> dict | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    role_name = None
    permissions = []
    if user.role is not None:
        role_name = user.role.name
        permissions = sorted(
            permission.code for permission in user.role.permissions
        )

    return {
        "user_id": user.id,
        "username": user.username,
        "role": role_name,
        "permissions": permissions,
    }
