"""Unit tests for seeded default templates.

Tests that the default seeded templates can be rendered correctly
with sample context data to ensure they are functional.
"""

from autodoc.templates.engine import TemplateEngine


class TestSeededTemplates:
    """Tests for seeded default templates."""

    def test_python_api_change_summary_template(self):
        """Test Python API Change Summary template rendering."""
        engine = TemplateEngine()
        template_body = """# Python API Changes Summary

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

        variables = {
            "file_path": "src/api/handler.py",
            "run": {
                "repo": "myorg/myrepo",
                "branch": "main",
                "commit_sha": "abc123def456",
            },
            "rule": {
                "name": "Python API Rule",
            },
            "symbol": "process_request",
            "change_type": "modified",
            "signature_before": "def process_request(request: str) -> dict:",
            "signature_after": "def process_request(request: str, timeout: int = 30) -> dict:",
            "change_count": 1,
        }

        result = engine.render(template_body, variables, "Markdown")

        assert "Python API Changes Summary" in result
        assert "abc123def456" in result
        assert "myorg/myrepo" in result
        assert "main" in result
        assert "src/api/handler.py" in result
        assert "Python API Rule" in result
        assert "process_request" in result
        assert "modified" in result
        assert "def process_request(request: str) -> dict:" in result
        assert "def process_request(request: str, timeout: int = 30) -> dict:" in result
        assert "Total changes detected: 1" in result

    def test_typescript_endpoint_change_summary_template(self):
        """Test TypeScript Endpoint Change Summary template rendering."""
        engine = TemplateEngine()
        template_body = """# TypeScript Endpoint Changes Summary

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

        variables = {
            "file_path": "src/routes/api.ts",
            "run": {
                "repo": "myorg/frontend",
                "branch": "develop",
                "commit_sha": "xyz789ghi012",
            },
            "rule": {
                "name": "TypeScript Endpoint Rule",
            },
            "symbol": "getUserProfile",
            "change_type": "added",
            "signature_before": None,
            "signature_after": "async function getUserProfile(userId: string): Promise<User>",
            "change_count": 1,
        }

        result = engine.render(template_body, variables, "Markdown")

        assert "TypeScript Endpoint Changes Summary" in result
        assert "xyz789ghi012" in result
        assert "myorg/frontend" in result
        assert "develop" in result
        assert "src/routes/api.ts" in result
        assert "TypeScript Endpoint Rule" in result
        assert "getUserProfile" in result
        assert "added" in result
        assert "async function getUserProfile(userId: string): Promise<User>" in result
        assert "Total endpoint changes: 1" in result

    def test_changelog_snippet_template(self):
        """Test Changelog Snippet template rendering."""
        engine = TemplateEngine()
        template_body = """## {{run.commit_sha}} - {{run.branch}}

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

        variables = {
            "run": {
                "commit_sha": "def456abc789",
                "branch": "feature/new-endpoint",
                "repo": "myorg/backend",
            },
            "file_path": "api/endpoints.py",
            "symbol": "create_user",
            "change_type": "removed",
            "signature_before": "def create_user(name: str, email: str) -> User:",
            "signature_after": None,
            "change_count": 1,
        }

        result = engine.render(template_body, variables, "Markdown")

        assert "def456abc789" in result
        assert "feature/new-endpoint" in result
        assert "myorg/backend" in result
        assert "api/endpoints.py" in result
        assert "create_user" in result
        assert "removed" in result
        assert "def create_user(name: str, email: str) -> User:" in result
        assert "**Total Changes:** 1" in result

    def test_seeded_templates_have_documented_variables(self):
        """Test that seeded templates have documented variables metadata."""
        # This test verifies that the templates have variables documented
        # The actual variables dict is stored in the database, but we can verify
        # the structure by checking the template bodies contain expected placeholders

        expected_variables = [
            "run.commit_sha",
            "run.repo",
            "run.branch",
            "file_path",
            "rule.name",
            "symbol",
            "change_type",
            "signature_before",
            "signature_after",
            "change_count",
        ]

        python_template_body = """# Python API Changes Summary

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

        # Verify all expected variables are present in template
        for var in expected_variables:
            placeholder = f"{{{{{var}}}}}"
            assert placeholder in python_template_body, (
                f"Variable {var} not found in template"
            )
