"""Let the teacher practice on the same account without changing their role.

Revision ID: 20261018_0003
Revises: 20260807_0002
Create Date: 2026-10-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_0003"
down_revision: str | None = "20260807_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("study_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "study_mode", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "study_mode")
