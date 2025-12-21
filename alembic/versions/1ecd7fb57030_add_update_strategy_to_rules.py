"""add_update_strategy_to_rules

Revision ID: 1ecd7fb57030
Revises: add_javascript_go_symbols_tables
Create Date: 2025-12-20 18:15:53.339556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ecd7fb57030'
down_revision: Union[str, Sequence[str], None] = 'add_javascript_go_symbols_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rules', sa.Column('update_strategy', sa.Text(), nullable=False, server_default='replace'))
    op.create_check_constraint(
        'check_update_strategy',
        'rules',
        "update_strategy IN ('replace', 'append', 'modify_section')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('check_update_strategy', 'rules', type_='check')
    op.drop_column('rules', 'update_strategy')
