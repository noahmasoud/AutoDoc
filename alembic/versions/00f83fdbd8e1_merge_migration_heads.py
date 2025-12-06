"""Merge migration heads

Revision ID: 00f83fdbd8e1
Revises: 781f18a4db87, ab4e828d8044
Create Date: 2025-12-03 20:48:17.966674

"""

from typing import Sequence


# revision identifiers, used by Alembic.
revision: str = "00f83fdbd8e1"
down_revision: str | Sequence[str] | None = ("781f18a4db87", "ab4e828d8044")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
