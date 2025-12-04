"""add error status and error_message to patches

Revision ID: add_error_patch_status
Revises: 868644b39783
Create Date: 2025-01-27 14:00:00.000000

Per FR-24 and NFR-3/NFR-4: Support graceful error handling for template rendering failures.
Adds ERROR status and structured error_message field to patches.

"""

from collections.abc import Sequence
from contextlib import suppress

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_error_patch_status"
down_revision: str | Sequence[str] | None = "868644b39783"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add error_message column to patches table
    op.add_column(
        "patches",
        sa.Column("error_message", sa.JSON(), nullable=True),
    )

    # Update check constraint to include ERROR status
    # Note: SQLite has limited ALTER TABLE support for constraints.
    # The constraint is enforced at the application level by SQLAlchemy.
    # For production databases, this would require constraint recreation.
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        # For PostgreSQL and other databases, update the constraint
        with suppress(Exception):
            # Constraint might not exist or have different name
            op.drop_constraint("check_patch_status", "patches", type_="check")

        op.create_check_constraint(
            "check_patch_status",
            "patches",
            "status IN ('Proposed', 'Approved', 'Rejected', 'Applied', 'RolledBack', 'ERROR')",
        )
    # For SQLite, constraint enforcement is handled by SQLAlchemy model


def downgrade() -> None:
    """Downgrade schema."""
    # Remove error_message column
    op.drop_column("patches", "error_message")

    # Restore original constraint (if not SQLite)
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        with suppress(Exception):
            # Constraint might not exist
            op.drop_constraint("check_patch_status", "patches", type_="check")
            op.create_check_constraint(
                "check_patch_status",
                "patches",
                "status IN ('Proposed', 'Approved', 'Rejected', 'Applied', 'RolledBack')",
            )
