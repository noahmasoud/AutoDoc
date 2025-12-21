"""Add JavaScript and Go symbols tables

Revision ID: add_javascript_go_symbols_tables
Revises: 9945123fa3a0
Create Date: 2025-01-15 14:00:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_javascript_go_symbols_tables"
down_revision: str | Sequence[str] | None = "9945123fa3a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create javascript_symbols and go_symbols tables."""
    # Create javascript_symbols table
    op.create_table(
        "javascript_symbols",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("symbol_name", sa.Text(), nullable=False),
        sa.Column("qualified_name", sa.Text(), nullable=False),
        sa.Column("symbol_type", sa.Text(), nullable=False),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("lineno", sa.Integer(), nullable=True),
        sa.Column("symbol_metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "symbol_type IN ('module', 'class', 'function', 'method', 'interface', 'type', 'enum')",
            name="check_javascript_symbol_type",
        ),
        sa.UniqueConstraint(
            "run_id",
            "qualified_name",
            name="uq_javascript_symbols_run_path_name",
        ),
    )
    op.create_index(
        op.f("ix_javascript_symbols_run_id"),
        "javascript_symbols",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_javascript_symbols_file_path"),
        "javascript_symbols",
        ["file_path"],
        unique=False,
    )

    # Create go_symbols table
    op.create_table(
        "go_symbols",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("symbol_name", sa.Text(), nullable=False),
        sa.Column("qualified_name", sa.Text(), nullable=False),
        sa.Column("symbol_type", sa.Text(), nullable=False),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("lineno", sa.Integer(), nullable=True),
        sa.Column("symbol_metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "symbol_type IN ('package', 'function', 'method', 'type', 'interface', 'struct', 'const', 'var')",
            name="check_go_symbol_type",
        ),
        sa.UniqueConstraint(
            "run_id",
            "qualified_name",
            name="uq_go_symbols_run_path_name",
        ),
    )
    op.create_index(
        op.f("ix_go_symbols_run_id"),
        "go_symbols",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_go_symbols_file_path"),
        "go_symbols",
        ["file_path"],
        unique=False,
    )


def downgrade() -> None:
    """Remove javascript_symbols and go_symbols tables."""
    op.drop_index(op.f("ix_go_symbols_file_path"), table_name="go_symbols")
    op.drop_index(op.f("ix_go_symbols_run_id"), table_name="go_symbols")
    op.drop_table("go_symbols")
    op.drop_index(op.f("ix_javascript_symbols_file_path"), table_name="javascript_symbols")
    op.drop_index(op.f("ix_javascript_symbols_run_id"), table_name="javascript_symbols")
    op.drop_table("javascript_symbols")

