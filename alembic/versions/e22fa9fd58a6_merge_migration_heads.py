"""Merge migration heads

Revision ID: e22fa9fd58a6
Revises: 781f18a4db87, ab4e828d8044
Create Date: 2025-12-03 23:54:36.045326

"""

from typing import Sequence


# revision identifiers, used by Alembic.
revision: str = "e22fa9fd58a6"
down_revision: str | Sequence[str] | None = ("781f18a4db87", "ab4e828d8044")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
