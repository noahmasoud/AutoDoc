"""Add prompt_id to rules table

Revision ID: add_prompt_id_to_rules
Revises: update_default_prompts
Create Date: 2025-12-13 22:55:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_prompt_id_to_rules"
down_revision: str | Sequence[str] | None = "update_default_prompts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add prompt_id foreign key column to rules table."""
    # Add prompt_id column to rules table
    op.add_column(
        "rules",
        sa.Column(
            "prompt_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_rules_prompt_id",
        "rules",
        "prompts",
        ["prompt_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove prompt_id column from rules table."""
    # Drop foreign key constraint
    op.drop_constraint("fk_rules_prompt_id", "rules", type_="foreignkey")
    
    # Drop prompt_id column
    op.drop_column("rules", "prompt_id")

