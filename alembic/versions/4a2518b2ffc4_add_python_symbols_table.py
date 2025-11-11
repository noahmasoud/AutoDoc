"""add python symbols table

Revision ID: 4a2518b2ffc4
Revises: e166c3632866
Create Date: 2025-11-11 15:10:47.902194

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a2518b2ffc4"
down_revision: str | Sequence[str] | None = "e166c3632866"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "python_symbols",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("symbol_name", sa.Text(), nullable=False),
        sa.Column("qualified_name", sa.Text(), nullable=False),
        sa.Column("symbol_type", sa.Text(), nullable=False),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("lineno", sa.Integer(), nullable=True),
        sa.Column("symbol_metadata", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "symbol_type IN ('module', 'class', 'function', 'method')",
            name="check_python_symbol_type",
        ),
    )
    op.create_index(
        "ix_python_symbols_run_id",
        "python_symbols",
        ["run_id"],
    )
    op.create_index(
        "ix_python_symbols_file_path",
        "python_symbols",
        ["file_path"],
    )
    op.create_unique_constraint(
        "uq_python_symbols_run_path_name",
        "python_symbols",
        ["run_id", "qualified_name"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_python_symbols_run_path_name",
        "python_symbols",
        type_="unique",
    )
    op.drop_index("ix_python_symbols_file_path", table_name="python_symbols")
    op.drop_index("ix_python_symbols_run_id", table_name="python_symbols")
    op.drop_table("python_symbols")
