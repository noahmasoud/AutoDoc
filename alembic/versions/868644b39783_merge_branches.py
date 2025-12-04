"""merge_branches

Revision ID: 868644b39783
Revises: 781f18a4db87, a1b2c3d4e5f6
Create Date: 2025-12-02 11:57:50.603349

"""

from typing import Sequence


# revision identifiers, used by Alembic.
revision: str = "868644b39783"
down_revision: str | Sequence[str] | None = ("781f18a4db87", "a1b2c3d4e5f6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
