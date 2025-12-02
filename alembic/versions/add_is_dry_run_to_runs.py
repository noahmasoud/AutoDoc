"""add is_dry_run to runs

Revision ID: add_is_dry_run_to_runs
Revises: add_error_patch_status
Create Date: 2025-01-27 15:00:00.000000

Per FR-14 and UC-4: Support dry-run mode for generating patches without updating Confluence.
Adds is_dry_run boolean field to runs table.

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_is_dry_run_to_runs"
down_revision: str | Sequence[str] | None = "add_error_patch_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_dry_run column to runs table
    op.add_column(
        "runs",
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_dry_run column
    op.drop_column("runs", "is_dry_run")
