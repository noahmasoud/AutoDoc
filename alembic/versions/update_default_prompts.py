"""Update default prompts to target specific audiences

Revision ID: update_default_prompts
Revises: add_prompts_table
Create Date: 2025-12-13 20:00:00.000000

"""

from typing import Sequence

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "update_default_prompts"
down_revision: str | Sequence[str] | None = "add_prompts_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update default prompts to target specific audiences."""
    connection = op.get_bind()
    
    # Update Prompt 1: Development Team / Sprint Focus
    prompt_1_content = """As a senior developer reviewing code changes during a sprint, analyze these changes and provide a technical summary for the development team.

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
        UPDATE prompts 
        SET name = :name, content = :content 
        WHERE name IN ('Comprehensive Summary', 'Development Team / Sprint Focus')
        AND is_default = 1
        """),
        {
            "name": "Development Team / Sprint Focus",
            "content": prompt_1_content,
        },
    )
    
    # Update Prompt 2: Product Manager Focus
    prompt_2_content = """As a product manager reviewing code changes, analyze these updates and provide a business-focused summary.

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
        UPDATE prompts 
        SET name = :name, content = :content 
        WHERE name IN ('Technical Deep Dive', 'Product Manager Focus')
        AND is_default = 1
        """),
        {
            "name": "Product Manager Focus",
            "content": prompt_2_content,
        },
    )
    
    # Update Prompt 3: Tech Support Team Focus
    prompt_3_content = """As a technical support specialist reviewing code changes, analyze these updates and provide a support-focused summary.

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
        UPDATE prompts 
        SET name = :name, content = :content 
        WHERE name IN ('Executive Summary', 'Tech Support Team Focus')
        AND is_default = 1
        """),
        {
            "name": "Tech Support Team Focus",
            "content": prompt_3_content,
        },
    )
    
    # If prompts don't exist yet (migration hasn't run), insert them
    # Check if any default prompts exist
    result = connection.execute(text("SELECT COUNT(*) FROM prompts WHERE is_default = 1")).scalar()
    if result == 0:
        # Insert the prompts (same as add_prompts_table migration)
        from datetime import datetime
        now = datetime.utcnow()
        
        connection.execute(
            text("""
            INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
            VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
            """),
            {
                "name": "Development Team / Sprint Focus",
                "content": prompt_1_content,
                "is_default": True,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )
        
        connection.execute(
            text("""
            INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
            VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
            """),
            {
                "name": "Product Manager Focus",
                "content": prompt_2_content,
                "is_default": True,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )
        
        connection.execute(
            text("""
            INSERT INTO prompts (name, content, is_default, is_active, created_at, updated_at)
            VALUES (:name, :content, :is_default, :is_active, :created_at, :updated_at)
            """),
            {
                "name": "Tech Support Team Focus",
                "content": prompt_3_content,
                "is_default": True,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    """Revert to original default prompts."""
    connection = op.get_bind()
    
    # Revert to original names and content
    original_prompt_1 = """Please analyze the following code changes and provide a comprehensive summary.

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
    
    original_prompt_2 = """As a senior software engineer, analyze these code changes and provide a technical deep dive.

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
    
    original_prompt_3 = """Provide an executive-level summary of the following code changes.

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
        UPDATE prompts 
        SET name = 'Comprehensive Summary', content = :content 
        WHERE name = 'Development Team / Sprint Focus' AND is_default = 1
        """),
        {"content": original_prompt_1},
    )
    
    connection.execute(
        text("""
        UPDATE prompts 
        SET name = 'Technical Deep Dive', content = :content 
        WHERE name = 'Product Manager Focus' AND is_default = 1
        """),
        {"content": original_prompt_2},
    )
    
    connection.execute(
        text("""
        UPDATE prompts 
        SET name = 'Executive Summary', content = :content 
        WHERE name = 'Tech Support Team Focus' AND is_default = 1
        """),
        {"content": original_prompt_3},
    )

