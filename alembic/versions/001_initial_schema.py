"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_users_user_id", "users", ["user_id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"], unique=False)
    op.create_index("ix_transactions_user_created", "transactions", ["user_id", "created_at"], unique=False)
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_user_created", table_name="transactions")
    op.drop_index("ix_transactions_created_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_users_user_id", table_name="users")
    op.drop_table("users")
