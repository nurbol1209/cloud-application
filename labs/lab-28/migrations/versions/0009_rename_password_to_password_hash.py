"""rename password to password hash

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-17

Переименование столбца без потери данных: существующие учебные
пароли затем преобразуются scripts/hash_existing_passwords.py.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "password",
        new_column_name="password_hash",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "password_hash",
        new_column_name="password",
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
