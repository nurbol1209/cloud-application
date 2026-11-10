"""add role access model

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-10

Роли, разрешения и связь пользователя с ролью.
users.role_id допускает NULL: существующие пользователи получают
роль viewer скриптом scripts/init_access.py.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("role_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_users_role_id_roles",
            "roles",
            ["role_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint(
            "fk_users_role_id_roles",
            type_="foreignkey",
        )
        batch_op.drop_column("role_id")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
