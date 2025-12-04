"""add priority to rules

Revision ID: 781f18a4db87
Revises: 4a2518b2ffc4
Create Date: 2025-01-27 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "781f18a4db87"
down_revision: str | Sequence[str] | None = "4a2518b2ffc4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists (may have been added by ab4e828d8044)
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("rules")]

    if "priority" not in columns:
        op.add_column(
            "rules",
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rules", "priority")
