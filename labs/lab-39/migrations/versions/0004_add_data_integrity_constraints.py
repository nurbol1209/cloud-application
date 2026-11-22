"""add data integrity constraints

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("service_types") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=50),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_service_types_name",
            ["name"],
        )

    with op.batch_alter_table("services") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=100),
            nullable=False,
        )
        batch_op.alter_column(
            "type_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_services_status",
            "status IN ('running', 'maintenance', 'stopped')",
        )


def downgrade() -> None:
    with op.batch_alter_table("services") as batch_op:
        batch_op.drop_constraint(
            "ck_services_status",
            type_="check",
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            nullable=True,
        )
        batch_op.alter_column(
            "type_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=100),
            nullable=True,
        )

    with op.batch_alter_table("service_types") as batch_op:
        batch_op.drop_constraint(
            "uq_service_types_name",
            type_="unique",
        )
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=50),
            nullable=True,
        )
