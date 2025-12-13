"""Add prompts table

Revision ID: add_prompts_table
Revises: bcff3e1f3440
Create Date: 2025-12-09 12:00:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = "add_prompts_table"
down_revision: str | Sequence[str] | None = "bcff3e1f3440"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create prompts table and seed 3 default prompts."""
    # Create prompts table
    op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_prompts_name"), "prompts", ["name"], unique=True)
    
    # Seed 3 default prompts
    connection = op.get_bind()
    now = datetime.utcnow()
    
    # Default Prompt 1: Comprehensive Summary
    default_prompt_1_content = """Please analyze the following code changes and provide a comprehensive summary.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Number of patches: {patches_count}

Patches:
{patches_text}

Please provide:
1. A brief summary of what was changed
2. A detailed description of the changes
3. An explanation of how demo_api.py runs and what it does
4. Any important notes or considerations

Format your response with clear sections for easy parsing."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Comprehensive Summary",
            "content": default_prompt_1_content,
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    
    # Default Prompt 2: Technical Deep Dive
    default_prompt_2_content = """As a senior software engineer, analyze these code changes and provide a technical deep dive.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Patches: {patches_count}

Code Changes:
{patches_text}

Provide:
1. Technical summary of code modifications
2. Impact analysis on existing functionality
3. Potential risks or breaking changes
4. Recommendations for testing and review
5. Dependencies and integration points affected

Use technical terminology and be specific about code patterns and architectural implications."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Technical Deep Dive",
            "content": default_prompt_2_content,
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    
    # Default Prompt 3: Executive Summary
    default_prompt_3_content = """Provide an executive-level summary of the following code changes.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Changes: {patches_count} patches

Overview:
{patches_text}

Please provide:
1. High-level summary (2-3 sentences)
2. Business impact and value delivered
3. Key changes in non-technical terms
4. Next steps or actions required

Keep the summary concise, clear, and accessible to non-technical stakeholders."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Executive Summary",
            "content": default_prompt_3_content,
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )


def downgrade() -> None:
    """Remove prompts table and all data."""
    op.drop_index(op.f("ix_prompts_name"), table_name="prompts")
    op.drop_table("prompts")

