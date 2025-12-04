"""seed default templates

Revision ID: a1b2c3d4e5f6
Revises: 781f18a4db87
Create Date: 2025-01-27 13:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "ab4e828d8044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Seed default templates for common documentation scenarios."""
    import json

    connection = op.get_bind()

    # Template 1: Python API Change Summary
    # Works best for single changes, uses individual variables when available
    python_api_template_body = """# Python API Changes Summary

## Overview
This document summarizes changes to the Python API in commit {{run.commit_sha}}.

**Repository:** {{run.repo}}
**Branch:** {{run.branch}}
**File:** `{{file_path}}`
**Rule:** {{rule.name}}

## Change Details

**Symbol:** `{{symbol}}`
**Change Type:** {{change_type}}

**Previous Signature:**
```python
{{signature_before}}
```

**New Signature:**
```python
{{signature_after}}
```

## Summary
Total changes detected: {{change_count}}

---
*Generated automatically by AutoDoc*"""

    python_api_variables = {
        "file_path": "Path to the changed file",
        "run.repo": "Repository name",
        "run.branch": "Branch name",
        "run.commit_sha": "Commit SHA hash",
        "rule.name": "Name of the matching rule",
        "symbol": "Name of the changed symbol (function, class, method)",
        "change_type": "Type of change: 'added', 'removed', or 'modified'",
        "signature_before": "Previous function/class signature (if modified or removed)",
        "signature_after": "New function/class signature (if added or modified)",
        "change_count": "Total number of changes detected",
    }

    connection = op.get_bind()
    connection.execute(
        text("""
        INSERT INTO templates (name, format, body, variables)
        VALUES (
            'Python API Change Summary',
            'Markdown',
            :body,
            :variables
        )
        """),
        {
            "body": python_api_template_body,
            "variables": json.dumps(python_api_variables),
        },
    )

    # Template 2: TypeScript Endpoint Change Summary
    typescript_endpoint_template_body = """# TypeScript Endpoint Changes Summary

## Overview
This document summarizes changes to TypeScript endpoints in commit {{run.commit_sha}}.

**Repository:** {{run.repo}}
**Branch:** {{run.branch}}
**File:** `{{file_path}}`
**Rule:** {{rule.name}}

## Endpoint Change

**Symbol:** `{{symbol}}`
**Change Type:** {{change_type}}

**Previous Signature:**
```typescript
{{signature_before}}
```

**New Signature:**
```typescript
{{signature_after}}
```

## Summary
Total endpoint changes: {{change_count}}

---
*Generated automatically by AutoDoc*"""

    typescript_endpoint_variables = {
        "file_path": "Path to the changed file",
        "run.repo": "Repository name",
        "run.branch": "Branch name",
        "run.commit_sha": "Commit SHA hash",
        "rule.name": "Name of the matching rule",
        "symbol": "Name of the changed endpoint/function",
        "change_type": "Type of change: 'added', 'removed', or 'modified'",
        "signature_before": "Previous endpoint signature (if modified or removed)",
        "signature_after": "New endpoint signature (if added or modified)",
        "change_count": "Total number of endpoint changes detected",
    }

    connection.execute(
        text("""
        INSERT INTO templates (name, format, body, variables)
        VALUES (
            'TypeScript Endpoint Change Summary',
            'Markdown',
            :body,
            :variables
        )
        """),
        {
            "body": typescript_endpoint_template_body,
            "variables": json.dumps(typescript_endpoint_variables),
        },
    )

    # Template 3: Changelog Snippet
    changelog_template_body = """## {{run.commit_sha}} - {{run.branch}}

**Repository:** {{run.repo}}
**File:** `{{file_path}}`

### Changes

**Symbol:** `{{symbol}}`
**Type:** {{change_type}}

**Previous:**
```
{{signature_before}}
```

**New:**
```
{{signature_after}}
```

**Total Changes:** {{change_count}}

---"""

    changelog_variables = {
        "run.commit_sha": "Full commit SHA hash",
        "run.branch": "Branch name",
        "run.repo": "Repository name",
        "file_path": "Path to the changed file",
        "symbol": "Name of the changed symbol",
        "change_type": "Type of change: 'added', 'removed', or 'modified'",
        "signature_before": "Previous signature (if modified or removed)",
        "signature_after": "New signature (if added or modified)",
        "change_count": "Total number of changes",
    }

    connection.execute(
        text("""
        INSERT INTO templates (name, format, body, variables)
        VALUES (
            'Changelog Snippet',
            'Markdown',
            :body,
            :variables
        )
        """),
        {
            "body": changelog_template_body,
            "variables": json.dumps(changelog_variables),
        },
    )


def downgrade() -> None:
    """Remove seeded default templates."""
    op.execute(
        text("""
        DELETE FROM templates
        WHERE name IN (
            'Python API Change Summary',
            'TypeScript Endpoint Change Summary',
            'Changelog Snippet'
        )
        """)
    )
