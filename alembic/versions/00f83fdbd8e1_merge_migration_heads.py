"""Merge migration heads

Revision ID: 00f83fdbd8e1
Revises: 781f18a4db87, ab4e828d8044
Create Date: 2025-12-03 20:48:17.966674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00f83fdbd8e1'
down_revision: Union[str, Sequence[str], None] = ('781f18a4db87', 'ab4e828d8044')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
