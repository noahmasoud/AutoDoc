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
    
    # Default Prompt 1: Development Team / Sprint Focus
    default_prompt_1_content = """As a senior developer reviewing code changes during a sprint, analyze these changes and provide a technical summary for the development team.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Number of patches: {patches_count}

Code Changes:
{patches_text}

Please provide:
1. **Sprint Impact Summary**: What functionality was added, modified, or removed? How does this affect current sprint goals?
2. **Technical Details**: Specific code changes, patterns used, and architectural implications
3. **Integration Points**: What other parts of the codebase might be affected? Any breaking changes?
4. **Testing Recommendations**: What should be tested? Any edge cases or regression risks?
5. **Code Quality Notes**: Code style, performance considerations, or technical debt introduced
6. **Next Steps**: What follow-up work is needed? Any dependencies or blockers?

Focus on actionable technical information that helps the team understand the changes and plan their work."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Development Team / Sprint Focus",
            "content": default_prompt_1_content,
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    
    # Default Prompt 2: Product Manager Focus
    default_prompt_2_content = """As a product manager reviewing code changes, analyze these updates and provide a business-focused summary.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Number of patches: {patches_count}

Code Changes:
{patches_text}

Please provide:
1. **Feature Summary**: What user-facing features or capabilities were added, changed, or removed? Describe in business terms.
2. **User Impact**: How do these changes affect end users? Any new functionality, improvements, or removed features?
3. **Business Value**: What problem does this solve? What value does it deliver to customers or stakeholders?
4. **Release Readiness**: Is this ready for production? Any risks or considerations for deployment?
5. **Documentation Needs**: What documentation or communication is needed for users, support, or stakeholders?
6. **Metrics & Success Criteria**: What should we measure to determine if this change is successful?

Focus on business outcomes, user experience, and product strategy rather than technical implementation details."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Product Manager Focus",
            "content": default_prompt_2_content,
            "is_default": True,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )
    
    # Default Prompt 3: Tech Support Team Focus
    default_prompt_3_content = """As a technical support specialist reviewing code changes, analyze these updates and provide a support-focused summary.

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Number of patches: {patches_count}

Code Changes:
{patches_text}

Please provide:
1. **Support Impact Summary**: What changed from a support perspective? Any new features, fixes, or changes that affect users?
2. **Known Issues & Fixes**: What bugs were fixed? Are there any known issues or limitations introduced?
3. **User-Facing Changes**: What will users notice? Any new functionality, UI changes, or behavior modifications?
4. **Troubleshooting Guide**: What common issues might arise? How should support staff troubleshoot related problems?
5. **Documentation Updates**: What support documentation needs updating? Any new FAQs, troubleshooting steps, or user guides needed?
6. **Escalation Points**: When should support escalate to engineering? What technical details should support be aware of?

Focus on practical information that helps support teams assist users and resolve issues effectively."""
    
    connection.execute(
        text("""
        INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
        VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
        """),
        {
            "name": "Tech Support Team Focus",
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

