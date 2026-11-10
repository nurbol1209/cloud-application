"""baseline existing schema

Revision ID: 0001
Revises:
Create Date: 2026-10-20

Исходная структура БД была создана SQL-скриптами ЛР № 14.
Baseline только фиксирует её как начальное состояние Alembic.
"""

from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
