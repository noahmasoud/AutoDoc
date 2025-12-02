# Template Engine Documentation

## Overview

The AutoDoc template engine provides variable substitution for generating Confluence documentation patches. Templates support placeholders that are replaced with actual values during rendering.

## Placeholder Convention

### Basic Syntax

Templates use double curly braces `{{variable_name}}` to denote placeholders that will be replaced during rendering.

### Simple Variables

Simple variables are replaced directly:

```
Hello {{name}}, welcome to {{project}}!
```

With variables `{"name": "AutoDoc", "project": "Documentation"}`:
```
Hello AutoDoc, welcome to Documentation!
```

### Nested Object Access

Nested object properties can be accessed using dot notation:

```
The function {{symbol.name}} is located at {{symbol.file_path}}.
```

With variables:
```json
{
  "symbol": {
    "name": "process_request",
    "file_path": "src/api.py"
  }
}
```

Result:
```
The function process_request is located at src/api.py.
```

### Multiple Levels of Nesting

Nested access supports multiple levels:

```
{{change.symbol.name}} was {{change.type}} in {{change.file.path}}.
```

### Missing Variables

If a variable is not provided in the context:
- The placeholder is left unchanged in the output (e.g., `{{missing_var}}` remains as-is)
- This behavior may be improved in future versions (S3-4) to provide better error handling

### Examples

#### Example 1: Simple Template

**Template:**
```
# API Changes

**File:** {{file_path}}
**Symbol:** {{symbol_name}}
**Change Type:** {{change_type}}
```

**Variables:**
```json
{
  "file_path": "src/api.py",
  "symbol_name": "process_request",
  "change_type": "added"
}
```

**Rendered Output:**
```
# API Changes

**File:** src/api.py
**Symbol:** process_request
**Change Type:** added
```

#### Example 2: Nested Template

**Template:**
```
# Change Summary

**Symbol:** {{symbol.name}}
**Type:** {{symbol.type}}
**Location:** {{symbol.file_path}}:{{symbol.lineno}}
**Description:** {{symbol.docstring}}
```

**Variables:**
```json
{
  "symbol": {
    "name": "handle_error",
    "type": "function",
    "file_path": "src/api.py",
    "lineno": 42,
    "docstring": "Handles API errors gracefully"
  }
}
```

**Rendered Output:**
```
# Change Summary

**Symbol:** handle_error
**Type:** function
**Location:** src/api.py:42
**Description:** Handles API errors gracefully
```

#### Example 3: Multiple Changes

**Template:**
```
# Changes in {{file_path}}

{{#changes}}
- **{{symbol}}** ({{change_type}})
{{/changes}}
```

Note: List iteration is not yet supported in the initial implementation. This is a placeholder for future enhancement.

## Template Format

Templates support two formats as defined in the Template model:

- **Markdown**: Standard Markdown format for Confluence
- **Storage**: Confluence Storage Format (XML-based)

The template engine performs variable substitution regardless of format. The format is primarily used by downstream services to determine how to publish the rendered content to Confluence.

## Integration with Template Entity

Templates stored in the database (Template model) have the following structure:

- `id`: Unique identifier
- `name`: Template name
- `format`: Either "Markdown" or "Storage"
- `body`: The template content with placeholders
- `variables`: JSON object documenting expected variables (metadata only)

The `variables` field in the Template model is for documentation purposes and does not affect rendering. All variable substitution is performed using the `render()` method with a provided variable context.

## Usage

```python
from autodoc.templates.engine import TemplateEngine

engine = TemplateEngine()
template_body = "Hello {{name}}!"
variables = {"name": "World"}
rendered = engine.render(template_body, variables, format="Markdown")
# Result: "Hello World!"
```

## Future Enhancements

- Error handling for missing variables (S3-4)
- List iteration support
- Conditional blocks
- String formatting and filters

