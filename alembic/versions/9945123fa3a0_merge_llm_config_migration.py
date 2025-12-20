"""merge_llm_config_migration

Revision ID: 9945123fa3a0
Revises: 68bf4aa63d14, add_llm_configs_table
Create Date: 2025-12-18 20:53:43.625427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9945123fa3a0'
down_revision: Union[str, Sequence[str], None] = ('68bf4aa63d14', 'add_llm_configs_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
