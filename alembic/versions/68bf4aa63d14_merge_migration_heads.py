"""Merge migration heads

Revision ID: 68bf4aa63d14
Revises: 495f65cb96e2, 9ffc3641511e, add_is_dry_run_to_runs
Create Date: 2025-12-04 16:09:36.606545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68bf4aa63d14'
down_revision: Union[str, Sequence[str], None] = ('495f65cb96e2', '9ffc3641511e', 'add_is_dry_run_to_runs')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
