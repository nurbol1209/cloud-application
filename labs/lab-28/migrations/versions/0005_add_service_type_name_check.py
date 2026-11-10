"""add service type name check

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-27

Дополнительное задание: запрет пустого названия типа после TRIM.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("service_types") as batch_op:
        batch_op.create_check_constraint(
            "ck_service_types_name_not_empty",
            "TRIM(name) <> ''",
        )


def downgrade() -> None:
    with op.batch_alter_table("service_types") as batch_op:
        batch_op.drop_constraint(
            "ck_service_types_name_not_empty",
            type_="check",
        )
