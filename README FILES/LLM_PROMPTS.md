
### Prompt 1: Sprint 1 Infrastructure Planning

**MANDATORY CONTEXT:**
I am the Infrastructure Lead for AutoDoc, a CI/CD tool that automatically analyzes Python code changes and generates documentation updates for Confluence. This is a university capstone project with a 3-person team. I am new to infrastructure/DevOps and need step-by-step guidance.

**PROJECT REQUIREMENTS:**
- Analyze Python code changes between versions
- Extract functions, classes, methods, and parameters
- Capture docstrings for documentation generation
- Detect breaking changes (parameter removal, type changes, etc.)
- Output structured JSON for backend consumption
- Run in Docker containers via GitHub Actions

**SPRINT 1 TICKETS:**
1. SCRUM-26: AST Parser - Parse Python files to Abstract Syntax Tree
2. SCRUM-27: Symbol Extractor - Extract functions, classes, symbols
3. SCRUM-28: Change Detector - Compare versions and flag breaking changes
4. SCRUM-29: Docstring Extractor - Capture all documentation strings

**CRITICAL REQUEST:**
Create a **numbered list of modules** for the analysis engine. For each module provide:
1. Module file path and name
2. Function/class signatures (no implementation)
3. One-line docstring explaining purpose
4. Input/output types
5. Dependencies between modules

**MANDATORY REQUIREMENTS:**
- Use Python 3.10+ with type hints
- Use only Python standard library (ast, dataclasses, typing)
- Follow dataclass pattern for data structures
- Each module must have single responsibility
- Output must be JSON-serializable

**FORMAT:**
```
Module 1: [file_path]
  - Function: signature
    Purpose: one-line description
    Input: types
    Output: types
```

Do NOT include implementation code yet. Focus on architecture and interfaces.


**CRITICAL:** Ensure modules can work together in this pipeline:
Python Code → Parser → Extractor → Change Detector → JSON Output
### MANDATORY: Data Structure Planning (Prompt 2)

**CRITICAL CONTEXT:**
Building on the module architecture, I need to design the data structures that flow between modules in the AutoDoc analysis pipeline.

**PIPELINE FLOW:**
```
Python Source Code (str)
    ↓
AST (ast.Module)
    ↓
ModuleInfo (our structure)
    ↓
ChangeReport (our structure)
    ↓
JSON (dict)
```

**CRITICAL REQUEST:**
Design Python dataclasses for:

1. **ParameterInfo** - Function/method parameter
   - Must include: name, type annotation, default value, is_optional

2. **FunctionInfo** - Function or method
   - Must include: name, parameters, return type, decorators, docstring, line_number, is_public

3. **ClassInfo** - Class definition
   - Must include: name, base_classes, methods, docstring, line_number, is_public

4. **ModuleInfo** - Complete Python module
   - Must include: file_path, functions, classes, imports, module_docstring

5. **ChangeInfo** - Single detected change
   - Must include: change_type (added/removed/modified), symbol_type, symbol_name, is_breaking, breaking_reasons, details

6. **ChangeReport** - Full analysis report
   - Must include: file_path, old_version, new_version, added, removed, modified, has_breaking_changes, summary

**MANDATORY REQUIREMENTS:**
- Use @dataclass decorator
- Use type hints for all fields
- Include Optional[] for nullable fields
- Include default_factory for lists/dicts
- Add to_dict() method for JSON serialization

**FORMAT:**
```python
@dataclass
class StructureName:
    """One-line purpose"""
    field_name: FieldType
    optional_field: Optional[Type] = None
    list_field: List[Type] = field(default_factory=list)
```

**CRITICAL:** These structures must support the entire pipeline without modification.

### Prompt 2: Implement AST Parser Module

**MANDATORY CONTEXT:**
I am implementing SCRUM-26: AST Parser for the AutoDoc project. I have the architecture planned and data structures defined.

**MODULE SPECIFICATION:**
```python
# src/analyzer/parser.py

def parse_python_file(file_path: str) -> ast.Module:
    """Parse a Python file and return its AST."""
    
def parse_python_code(code: str) -> ast.Module:
    """Parse Python source code string and return its AST."""
```

**CRITICAL REQUIREMENTS:**
1. Read Python file from disk
2. Parse to AST using ast.parse()
3. Handle syntax errors gracefully
4. Support Python 3.10+ syntax
5. Preserve line numbers and structure

**MANDATORY ERROR HANDLING:**
- Catch SyntaxError with clear messages
- Catch FileNotFoundError with path information
- Return helpful error messages for debugging

**IMPLEMENTATION REQUEST:**
Provide the **complete implementation** of parser.py with:
- Full function implementations
- Comprehensive error handling
- Type hints
- Docstrings explaining each function
- Example usage in docstring

**CODE STRUCTURE:**
```python
import ast
from pathlib import Path
from typing import Optional

def parse_python_file(file_path: str) -> ast.Module:
    """[Complete this function]"""
    
def parse_python_code(code: str) -> ast.Module:
    """[Complete this function]"""
```

**CRITICAL:** The AST output must be compatible with Python's ast.NodeVisitor for the next module (Symbol Extractor).

Include example usage showing:
```python
# Example 1: Parse from file
tree = parse_python_file("example.py")

# Example 2: Parse from string
code = "def hello(): pass"
tree = parse_python_code(code)
```

**MANDATORY:** Implementation must be production-ready with proper error handling.


### Prompt 3: Implement Symbol Extractor with Visitor Pattern

**MANDATORY CONTEXT:**
I am implementing SCRUM-27: Symbol Extractor. This module must traverse an AST and extract all functions, classes, methods, and their metadata.

**PREVIOUS MODULE OUTPUT:**
The parser (SCRUM-26) provides: `ast.Module` object

**THIS MODULE OUTPUT:**
Must produce: `ModuleInfo` object containing all extracted symbols

**DATA STRUCTURES AVAILABLE:**
[Include the dataclass definitions from Prompt 1.2]

**CRITICAL REQUIREMENTS:**
1. Use ast.NodeVisitor pattern to traverse AST
2. Extract ALL functions (module-level and class methods)
3. Extract ALL classes with their methods
4. Filter out private symbols (names starting with _)
5. Capture parameter information with type hints
6. Capture return type annotations
7. Extract decorators
8. Record line numbers
9. Determine public vs private visibility

**MANDATORY IMPLEMENTATION PATTERN:**
```python
class SymbolExtractor(ast.NodeVisitor):
    """Visitor that extracts symbols from AST."""
    
    def __init__(self, file_path: str):
        """Initialize extractor."""
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function information."""
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class information."""
        
    def _extract_function_info(self, node: ast.FunctionDef) -> FunctionInfo:
        """Helper to create FunctionInfo from AST node."""
        
    def _extract_parameter_info(self, arg: ast.arg) -> ParameterInfo:
        """Helper to create ParameterInfo from AST arg."""

def extract_symbols(tree: ast.Module, file_path: str) -> ModuleInfo:
    """Main entry point: extract all symbols from AST."""
```

**CRITICAL REQUEST:**
Provide **complete implementation** with:
1. Full SymbolExtractor class with all visitor methods
2. Helper methods for parameter extraction
3. Type annotation extraction logic
4. Decorator handling
5. Public/private filtering
6. Main extract_symbols() function

**MANDATORY DETAILS:**
- Handle both positional and keyword arguments
- Extract default values for parameters
- Handle *args and **kwargs
- Extract type annotations from ast.arg.annotation
- Handle cases where annotations are missing

**CRITICAL:** The output ModuleInfo must be ready for comparison in the Change Detector module.

Include example showing extraction of this code:
```python
def get_user(user_id: int, active: bool = True) -> dict:
    """Get user by ID."""
    return {"id": user_id}
```

Expected output structure:
```python
FunctionInfo(
    name="get_user",
    parameters=[
        ParameterInfo(name="user_id", annotation="int", ...),
        ParameterInfo(name="active", annotation="bool", default=True, ...)
    ],
    return_type="dict",
    ...
)
```

**MANDATORY:** Implementation must handle edge cases and real-world Python code.


### Prompt 4: Enhance Symbol Extractor with Docstring Capture

**MANDATORY CONTEXT:**
I am implementing SCRUM-29: Extract Docstrings. This enhances SCRUM-27 by capturing all documentation strings.

**CURRENT STATE:**
Symbol Extractor (from SCRUM-27) extracts functions and classes but may not capture docstrings properly.

**CRITICAL REQUIREMENTS:**
1. Extract module-level docstrings
2. Extract function docstrings
3. Extract class docstrings
4. Extract method docstrings
5. Handle different docstring formats:
   - Google style (Args:, Returns:, Raises:)
   - NumPy style (Parameters, Returns sections)
   - reStructuredText style
   - Simple one-liners
6. Preserve formatting and structure
7. Handle missing docstrings gracefully

**MANDATORY IMPLEMENTATION:**
Update the SymbolExtractor class to use `ast.get_docstring()`:
```python
class SymbolExtractor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.module_docstring: Optional[str] = None  # ADD THIS
        ...
    
    def extract(self, tree: ast.Module) -> ModuleInfo:
        """Extract symbols and docstrings."""
        # CRITICAL: Extract module docstring first
        self.module_docstring = ast.get_docstring(tree)
        ...
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function with docstring."""
        # CRITICAL: Use ast.get_docstring(node)
        docstring = ast.get_docstring(node)
        ...
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class with docstring."""
        # CRITICAL: Use ast.get_docstring(node)
        docstring = ast.get_docstring(node)
        ...
```

**CRITICAL REQUEST:**
Show me the **complete updated implementation** with:
1. Module docstring extraction
2. Function docstring extraction  
3. Class docstring extraction
4. Method docstring extraction
5. Storage in appropriate dataclass fields

**TEST CASE:**
```python
"""
Module docstring.

This module does cool things.
"""

def example(x: int) -> str:
    """
    Function docstring.
    
    Args:
        x: An integer
        
    Returns:
        A string
    """
    return str(x)
```

Expected extraction:
```python
ModuleInfo(
    module_docstring="Module docstring.\n\nThis module does cool things.",
    functions=[
        FunctionInfo(
            name="example",
            docstring="Function docstring.\n\nArgs:\n    x: An integer\n    \nReturns:\n    A string",
            ...
        )
    ]
)
```

**MANDATORY:** Docstrings must be extracted as-is without modification, preserving all formatting.

### Prompt 5: Implement Change Detector with Breaking Change Analysis

**MANDATORY CONTEXT:**
I am implementing SCRUM-28: Change Detector. This is the core logic that compares two versions of code and identifies changes.

**INPUT:**
- `old_module: ModuleInfo` - Symbols from previous version
- `new_module: ModuleInfo` - Symbols from current version

**OUTPUT:**
- `ChangeReport` - Structured report of all changes with breaking change flags

**CRITICAL CHANGE DETECTION RULES:**

**BREAKING CHANGES:**
1. Function/method removed from public API
2. Required parameter removed
3. Required parameter added (no default value)
4. Parameter renamed
5. Parameter type changed
6. Return type changed (if not adding type to untyped)
7. Class removed from public API

**NON-BREAKING CHANGES:**
1. Optional parameter added (has default value)
2. New function/method added
3. New class added
4. Docstring changed
5. Type hint added to untyped parameter
6. Return type hint added where none existed
7. Private symbol changes (starting with _)

**MANDATORY IMPLEMENTATION STRUCTURE:**
```python
def detect_changes(
    old_module: ModuleInfo,
    new_module: ModuleInfo,
    old_version: str = "old",
    new_version: str = "new"
) -> ChangeReport:
    """
    Compare two module versions and detect changes.
    
    Returns ChangeReport with added, removed, and modified symbols.
    Breaking changes are flagged with reasons.
    """
    
def _compare_functions(
    old_func: FunctionInfo,
    new_func: FunctionInfo
) -> Optional[ChangeInfo]:
    """Compare two functions and return ChangeInfo if modified."""
    
def _compare_parameters(
    old_params: List[ParameterInfo],
    new_params: List[ParameterInfo]
) -> Tuple[bool, List[str]]:
    """
    Compare parameter lists.
    Returns (is_breaking, reasons).
    """
    
def _compare_classes(
    old_class: ClassInfo,
    new_class: ClassInfo
) -> Optional[ChangeInfo]:
    """Compare two classes and return ChangeInfo if modified."""
```

**CRITICAL ALGORITHM:**
1. Create dictionaries of old/new symbols by name
2. Find added symbols: `new_symbols.keys() - old_symbols.keys()`
3. Find removed symbols: `old_symbols.keys() - new_symbols.keys()`
4. Find common symbols: `old_symbols.keys() & new_symbols.keys()`
5. For each common symbol, deep compare and detect modifications
6. For modifications, apply breaking change rules
7. Build ChangeReport with all findings

**MANDATORY COMPARISON LOGIC:**

**For Functions:**
```python
# Compare parameters
old_param_names = {p.name for p in old_func.parameters}
new_param_names = {p.name for p in new_func.parameters}

# Parameter removed = BREAKING
removed_params = old_param_names - new_param_names
if removed_params:
    is_breaking = True
    reasons.append(f"Parameter '{param}' removed")

# Required parameter added = BREAKING
for new_param in new_func.parameters:
    if new_param.name not in old_param_names:
        if not new_param.default:  # No default value
            is_breaking = True
            reasons.append(f"Required parameter '{new_param.name}' added")

# Compare return types
if old_func.return_type != new_func.return_type:
    if old_func.return_type is not None:  # Type changed
        is_breaking = True
        reasons.append("Return type changed")
```

**CRITICAL REQUEST:**
Provide **complete implementation** of change_detector.py with:
1. Main detect_changes() function
2. Function comparison logic
3. Class comparison logic
4. Parameter comparison with breaking change detection
5. Method comparison for classes
6. Proper ChangeInfo and ChangeReport creation
7. Comprehensive breaking change rules

**TEST SCENARIO:**
```python
# Old version
def get_user(id):
    return {"id": id}

# New version  
def get_user(user_id: int, active: bool = True) -> dict:
    return {"id": user_id}
```

Expected detection:
```python
ChangeInfo(
    change_type="modified",
    symbol_name="get_user",
    is_breaking=True,
    breaking_reasons=[
        "Parameter 'id' removed",
        "Required parameter 'user_id' added"
    ],
    details={
        "optional_parameter_added": "active",
        "return_type_added": "dict"
    }
)
```

**MANDATORY:** All breaking change rules must be implemented correctly and consistently.

### Prompt 6: Create Test Suite for Change Detector

**MANDATORY CONTEXT:**
I need a comprehensive test suite for the change detector module (SCRUM-28) to achieve >95% coverage.

**TESTING REQUIREMENTS:**

**MANDATORY TEST CATEGORIES:**
1. Added symbols (functions, classes, methods)
2. Removed symbols (breaking changes)
3. Modified symbols (parameter changes, type changes)
4. Breaking vs non-breaking changes
5. Edge cases (empty modules, private symbols)
6. Docstring changes (non-breaking)

**CRITICAL TEST CASES:**

**Breaking Changes:**
- Parameter removed
- Required parameter added
- Parameter renamed
- Parameter type changed
- Return type changed
- Method removed from class
- Public function removed

**Non-Breaking Changes:**
- Optional parameter added
- New function added
- New method added
- Docstring updated
- Type hint added to untyped parameter
- Private symbol changes

**MANDATORY STRUCTURE:**
```python
# tests/unit/test_change_detector.py

import pytest
from src.analyzer.extractor import ModuleInfo, FunctionInfo, ParameterInfo
from src.analyzer.change_detector import detect_changes

def test_detect_parameter_removal():
    """Test that parameter removal is flagged as breaking."""
    # Setup old version
    old_module = ModuleInfo(...)
    
    # Setup new version
    new_module = ModuleInfo(...)
    
    # Detect changes
    report = detect_changes(old_module, new_module)
    
    # Assertions
    assert len(report.modified) == 1
    assert report.has_breaking_changes is True
    assert "Parameter 'x' removed" in report.modified[0].breaking_reasons

def test_optional_parameter_added():
    """Test that optional parameter is non-breaking."""
    ...

def test_required_parameter_added():
    """Test that required parameter is breaking."""
    ...
```

**CRITICAL REQUEST:**
Provide **30+ test cases** covering:
1. All breaking change scenarios
2. All non-breaking scenarios  
3. Edge cases
4. Class method changes
5. Multiple simultaneous changes

**MANDATORY:** Tests must be runnable with pytest and achieve >95% coverage.

Include test for this complex scenario:
```python
# Old
class Calculator:
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y

# New
class Calculator:
    def add(self, x: int, y: int) -> int:
        return x + y
    
    def calculate(self, op: str, x: int, y: int) -> int:
        # New method
        pass
```

Expected: 2 changes detected (1 modified, 1 added), breaking=False


**MANDATORY CONTEXT:**
I need to containerize the AutoDoc analysis engine and set up CI/CD in GitHub Actions.

**REQUIREMENTS:**

**Docker Image:**
- Base: python:3.11-slim
- Size: <500MB
- Build time: <5 minutes
- Multi-stage build for optimization
- Non-root user for security
- Contains all source code and dependencies

**GitHub Actions:**
- Build Docker image on push
- Run tests in container
- Publish to GitHub Container Registry (GHCR)
- Tag with commit SHA and 'latest'
- Only publish from main branch

**CRITICAL DOCKERFILE STRUCTURE:**
```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime  
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Create non-root user
RUN useradd -m -u 1000 autodoc && chown -R autodoc:autodoc /app
USER autodoc

# Entry point
COPY autodoc.sh ./
ENTRYPOINT ["./autodoc.sh"]
```

**CRITICAL GITHUB ACTIONS WORKFLOW:**
```yaml
name: Docker Image CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t autodoc:test .
      
      - name: Run tests
        run: docker run autodoc:test pytest tests/
      
      - name: Log in to GHCR
        if: github.ref == 'refs/heads/main'
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u $ --password-stdin
      
      - name: Push to GHCR
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag autodoc:test ghcr.io/${{ github.repository }}:latest
          docker push ghcr.io/${{ github.repository }}:latest
```

**MANDATORY REQUEST:**
Provide complete files for:
1. Dockerfile (multi-stage, optimized)
2. .github/workflows/docker-publish.yml (full workflow)
3. autodoc.sh (entry point script)
4. requirements.txt (if any external dependencies)

**CRITICAL:** Must work in GitHub Actions with minimal configuration.


### Prompt 7: Create Professional Sprint Demo Document

**MANDATORY CONTEXT:**
I need a professional markdown document to present Sprint 1 deliverables to my CS4398 class. The document will be used during a live presentation.

**AUDIENCE:**
- University professor
- Classmates (technical background)
- Evaluating sprint completion and technical depth

**SPRINT 1 DELIVERABLES:**
1. AST Parser (SCRUM-26)
2. Symbol Extractor (SCRUM-27)
3. Docstring Extractor (SCRUM-29)
4. Change Detector (SCRUM-28)
5. Test Suite (96.7% coverage, 30/31 tests)
6. Docker containerization
7. GitHub Actions CI/CD

**CRITICAL REQUIREMENTS:**

**Document Structure:**
1. Executive summary (what we built)
2. Demo scenario (clear use case)
3. Code examples (before/after versions)
4. Stage-by-stage walkthrough:
   - Stage 1: AST Parser (what, why, how)
   - Stage 2: Symbol Extractor (what, why, how)
   - Stage 3: Docstring Extractor (what, why, how)
   - Stage 4: Change Detector (what, why, how)
5. Final JSON output example
6. Sprint summary (deliverables, tech specs)
7. Architecture diagram
8. Next steps

**MANDATORY FOR EACH STAGE:**
- **"What it does"** - Clear explanation
- **"Why we need it"** - Business/technical justification
- **"How it works"** - Technical approach in bullet points
- **Example** - Code showing input/output

**CRITICAL EXAMPLE REQUIREMENTS:**
- Use a Calculator class (simple, obvious changes)
- Show method removed (breaking change)
- Show method added (non-breaking)
- Show parameter added (breaking vs non-breaking)
- Make impact crystal clear

**Example scenario:**
```python
# Version 1.0
class Calculator:
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y

# Version 2.0  
class Calculator:
    def calculate(self, operation: str, x: float, y: float) -> float:
        """Unified calculation method."""
        if operation == 'add':
            return x + y
        # ...
    
    def power(self, base: float, exp: float) -> float:
        """New: Raise to power."""
        return base ** exp
```

Changes: add() removed (BREAKING), subtract() removed (BREAKING), calculate() added, power() added

**MANDATORY FORMATTING:**
- Clear section headers with ##
- Code blocks with ```python
- Bullet points for lists
- Bold for emphasis on key points
- JSON examples properly formatted

**CRITICAL OUTPUT SECTIONS:**

**"This enables:"**
- Backend to ingest our JSON with human-readable text
- LLM to create guides from docstrings and enhance existing documentation or suggest new Confluence pages
- UI to show breaking changes to developers, allowing them to accept or decline the documentation
- Automated documentation updates on every commit

**"What We Delivered:"**
- Analysis Engine (Parser + Extractor + Detector)
- Docstring Extraction (Human-readable content)
- Breaking Change Detection (Smart comparison logic)
- JSON Output (Ready for backend integration)
- 96.7% Test Coverage (30/31 tests passing)
- Dockerized and CI/CD Ready Through GitHub Actions

**CRITICAL REQUEST:**
Create a complete SPRINT_1_DEMO.md file that:
1. Is professional and presentation-ready
2. Clearly explains technical concepts
3. Shows working examples
4. Demonstrates value delivered
5. Can be presented in 10-15 minutes
6. Impresses both technical and non-technical audience

**MANDATORY:** Document must be clear, concise, and compelling. No fluff, only substance.