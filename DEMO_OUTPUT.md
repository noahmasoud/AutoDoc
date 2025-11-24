# AutoDoc: Automated Documentation Pipeline

**Sprint 1 Demo - Analysis Engine**

---

## What We Built

**Our Goal:** Automatically update documentation when code changes

**Sprint 1 Deliverables:**
- AST Parser - Understands Python code structure
- Symbol Extractor - Finds functions, classes, parameters  
- Docstring Capture - Extracts human-readable descriptions
- Change Detector - Identifies breaking changes

**Output:** JSON file ready for backend to generate Confluence docs

---

## Demo Scenario

A developer updates a simple Calculator class:
- Changes method name (add → calculate)
- Adds required parameter
- Removes a method entirely
- Adds new functionality

**Let's see how AutoDoc detects these changes...**

---

## Version 1.0 (Before)
```python
# Basic Calculator 
class Calculator:    
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y
    
    def multiply(self, x, y):
        return x * y
```

---

## Version 2.0 (After)
```python

# Advanced calculator with extended operations.
# Supports basic arithmetic and memory storage.

  # Perform a calculation based on operation type.
  
  # Args:
  #     operation: Type of operation ('add', 'subtract', 'multiply')
  #     x: First number
  #     y: Second number
      
  # Returns:
  #     Result of the calculation
      
  # Raises:
  #     ValueError: If operation is not supported

class Calculator:
    
    def calculate(self, operation: str, x: float, y: float) -> float:
        if operation == 'add':
            return x + y
        elif operation == 'subtract':
            return x - y
        elif operation == 'multiply':
            return x * y
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def multiply(self, x: float, y: float) -> float:
        return x * y
    
    def power(self, base: float, exponent: float) -> float:
        return base ** exponent
```

**What changed:**
- `add()` method removed
- `subtract()` method removed  
- New `calculate()` method added (consolidated functionality)
- `multiply()` method modified (added type hints)
- `power()` method added (new functionality)

---

## Stage 1: Parse Python Code (AST Parser)

**What it does:**
Converts source code to Abstract Syntax Tree

**Results:**
```
✓ Old version parsed: Module with 1 top-level element (Calculator class)
✓ New version parsed: Module with 1 top-level element (Calculator class)
```

**Why?**  
AST lets us understand code structure programmatically, not just as text

**Example AST Structure:**
```
Module
└── ClassDef: "Calculator"
    ├── Docstring: "Simple calculator..."
    ├── FunctionDef: "add"
    ├── FunctionDef: "subtract"
    └── FunctionDef: "multiply"
```

---

## Stage 2: Extract Symbols (Functions, Classes)

**What it does:**
Extracts API surface from both versions

**Version 1.0 Extracted:**
```
Classes: 1
  • Calculator (3 methods)
    - add(x, y) -> None
    - subtract(x, y) -> None
    - multiply(x, y) -> None
```

**Version 2.0 Extracted:**
```
Classes: 1
  • Calculator (3 methods)
    - calculate(operation: str, x: float, y: float) -> float
    - multiply(x: float, y: float) -> float
    - power(base: float, exponent: float) -> float
```

**Why?**  
Creates structured view of API that can be compared

---

## Stage 3: Docstring Extraction (Human-Readable Content)

**What it does:**
Captures all documentation strings

**Class Docstring (v1.0):**
```
Simple calculator for basic math operations.
```

**Class Docstring (v2.0):**
```
Advanced calculator with extended operations.

Supports basic arithmetic and memory storage.
```

**Method Docstring Example (calculate):**
```
Perform a calculation based on operation type.

Args:
    operation: Type of operation ('add', 'subtract', 'multiply')
    x: First number
    y: Second number
    
Returns:
    Result of the calculation
    
Raises:
    ValueError: If operation is not supported
```

**Why?**  
- Docstrings become the content for documentation pages
- They give context to LLMs for better doc generation
- Makes automation produce human-readable output

---

## Stage 4: Change Detection (Breaking Changes)

**What it does:**
Compares versions to detect API changes

**Summary:**
```
Added: 2 methods (calculate, power)
Removed: 2 methods (add, subtract)
Modified: 1 method (multiply)
Breaking Changes: YES
```

**Detected Changes:**

### Class: Calculator
- **Breaking:** YES
- **Reasons:**
  - Method 'add' removed
  - Method 'subtract' removed

### Method: multiply (Modified)
- **Breaking:** NO
- **Changes:**
  - Type hints added (non-breaking)
  - Docstring updated (non-breaking)

### Method: calculate (Added)
- **Breaking:** NO
- **New functionality** - doesn't break existing code

### Method: power (Added)
- **Breaking:** NO
- **New functionality** - doesn't break existing code

**Why?**  
Breaking changes need migration guides for users

**Impact Example:**
```python
# Old code that will BREAK:
calc = Calculator()
result = calc.add(5, 3)  # ERROR: add() no longer exists

# Migration needed:
calc = Calculator()
result = calc.calculate('add', 5, 3)  # New way
```

---

## Final Output: change_report.json

**This JSON goes to the backend for doc generation:**
```json
{
  "file_path": "calculator.py",
  "added": [
    {
      "symbol": "calculate",
      "type": "method",
      "breaking": false
    },
    {
      "symbol": "power",
      "type": "method",
      "breaking": false
    }
  ],
  "removed": [
    {
      "symbol": "add",
      "type": "method",
      "breaking": true,
      "reason": "Method removed from public API"
    },
    {
      "symbol": "subtract",
      "type": "method",
      "breaking": true,
      "reason": "Method removed from public API"
    }
  ],
  "modified": [
    {
      "symbol": "multiply",
      "type": "method",
      "breaking": false,
      "reasons": [
        "Type hints added",
        "Docstring updated"
      ]
    }
  ],
  "summary": {
    "total_changes": 5,
    "added_count": 2,
    "removed_count": 2,
    "modified_count": 1,
    "breaking_count": 2
  }
}
```
**This enables:**
- Backend to ingest our JSON with human-readable text
- LLM to create guides from docstrings and enhance existing documentation or suggest new Confluence pages
- UI to show breaking changes to developers, allowing them to accept or decline the documentation
- Automated documentation updates on every commit

---

## Sprint 1 Complete

### What We Delivered:
- Analysis Engine (Parser + Extractor + Detector)
- Docstring Extraction (Human-readable content)
- Breaking Change Detection (Smart comparison logic)
- JSON Output (Ready for backend integration)
- 96.7% Test Coverage (30/31 tests passing)
- Dockerized and CI/CD Ready Through GitHub Actions

### Next Steps (Sprint 2+):
- Backend generates Confluence docs from JSON
- Confluence API integration
- Support for TypeScript files
- Frontend UI for reviewing changes

### Current Status:
**Infrastructure ready and integrated into CI/CD**

---

## Architecture Summary
```
Developer Commits Code
        ↓
GitHub Actions Triggered
        ↓
Docker Container Runs
        ↓
┌─────────────────────────────┐
│   Our Analysis Engine       │
│  ┌──────────────────────┐  │
│  │ 1. AST Parser        │  │
│  │ 2. Symbol Extractor  │  │
│  │ 3. Docstring Capture │  │
│  │ 4. Change Detector   │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
        ↓
change_report.json Generated
        ↓
Backend (Sprint 2) Processes
        ↓
Confluence Documentation Updated
```

---

## Questions?

**Key Takeaway:**  
We built the foundation that makes automated documentation possible. The analysis engine is ready and integrated into CI/CD.