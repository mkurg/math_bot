"""Add persistent live-lesson state for individual teaching.

Revision ID: 20260807_0002
Revises: 20260716_0001
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260807_0002"
down_revision: str | None = "20260716_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "student_settings",
        sa.Column(
            "live_lesson_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "student_settings",
        sa.Column(
            "live_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("student_settings", "live_lesson_enabled", server_default=None)
    op.alter_column("student_settings", "live_context", server_default=None)


def downgrade() -> None:
    op.drop_column("student_settings", "live_context")
    op.drop_column("student_settings", "live_lesson_enabled")
