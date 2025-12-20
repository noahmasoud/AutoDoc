"""Add LLM configs table

Revision ID: add_llm_configs_table
Revises: add_prompt_id_to_rules
Create Date: 2025-01-15 12:00:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_llm_configs_table"
down_revision: str | Sequence[str] | None = "add_prompt_id_to_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create llm_configs table."""
    op.create_table(
        "llm_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove llm_configs table."""
    op.drop_table("llm_configs")

