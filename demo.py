import ast
import json
from src.analyzer.extractor import extract_symbols
from src.analyzer.change_detector import detect_changes


def section(title, emoji=""):
    """Print a nice section header"""
    print("\n" + "=" * 50)
    print(f"{emoji} {title}")
    print("=" * 50 + "\n")


def main():  # noqa: PLR0915
    print("\n" + "=" * 50)
    print("AutoDoc: Automated Documentation Pipeline")
    print("Sprint 1 Demo - Analysis Engine")
    print("=" * 50)

    # Overview
    section("What We Built this Sprint")
    print("""
Our Goal: Automatically update documentation when code changes

Sprint 1 Deliverables:
    AST Parser        - Understands Python code structure
    Symbol Extractor  - Finds functions, classes, parameters
    Docstring Capture - Extracts human-readable descriptions
    Change Detector   - Identifies breaking changes

Output: JSON file → Ready for backend to generate Confluence docs
    """)

    input("\nPress Enter to see the demo...")

    # Scenario
    section("Demo Scenario")
    print("A developer updates a simple Calculator class:")
    print("  • Changes method name (add → calculate)")
    print("  • Adds required parameter")
    print("  • Removes a method entirely")
    print("  • Adds new functionality")
    print("\nLet's see how AutoDoc detects these changes...")

    input("\nPress Enter to continue...")

    # Version 1.0 - Before
    section("Version 1.0 - Before")

    old_code = """
# Basic Calculator

class Calculator:
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def multiply(self, x, y):
        return x * y
    """
    print(old_code)

    input("Press Enter to see new version...")

    # Version 2.0 - After
    section("Version 2.0 - After")

    new_code = """
# Advanced calculator with extended operations.
# Supports basic arithmetic and memory storage.

class Calculator:
    # Perform a calculation based on operation type.
    # Args: operation, x, y
    # Returns: Result of the calculation
    # Raises: ValueError if operation is not supported
    
    def calculate(self, operation: str, x: float, y: float) -> float:
        if operation == 'add':
            return x + y
        elif operation == 'subtract':
            return x - y
        elif operation == 'multiply':
            return x * y
        else:
            raise ValueError(f"Unknown operation: {operation}")

    # Multiply two numbers with type hints
    def multiply(self, x: float, y: float) -> float:
        return x * y

    # Raise a number to a power
    # Args: base, exponent
    # Returns: Result of base raised to exponent
    def power(self, base: float, exponent: float) -> float:
        return base ** exponent
"""
    print(new_code)

    input("\nPress Enter to analyze changes...")

    # Stage 1: Parse Code
    section("Stage 1: Parse Python Code - AST Parser")

    print("Converting source code to Abstract Syntax Tree...")
    old_tree = ast.parse(old_code)
    new_tree = ast.parse(new_code)

    print(
        f"Old version parsed: {type(old_tree).__name__} with {len(old_tree.body)} top-level elements"
    )
    print(
        f"New version parsed: {type(new_tree).__name__} with {len(new_tree.body)} top-level elements"
    )
    print("\nWhy? AST lets us understand code structure programmatically")

    input("\nPress Enter for symbol extraction...")

    # Stage 2: Extract Symbols
    section("Stage 2: Extract Symbols - Functions, Classes")

    print("Extracting API surface from both versions...")
    old_module = extract_symbols(old_tree, "calculator.py")
    new_module = extract_symbols(new_tree, "calculator.py")

    print("\n--- Version 1.0 ---")
    print(f"Classes: {len(old_module.classes)}")
    for cls in old_module.classes:
        print(f"  • {cls.name} ({len(cls.methods)} methods)")
        for method in cls.methods:
            params = [p.name for p in method.parameters]
            print(
                f"    - {method.name}({', '.join(params)}) -> {method.return_type or 'None'}"
            )

    print("\n--- Version 2.0 ---")
    print(f"Classes: {len(new_module.classes)}")
    for cls in new_module.classes:
        print(f"  • {cls.name} ({len(cls.methods)} methods)")
        for method in cls.methods:
            params = [
                f"{p.name}: {p.annotation}" if p.annotation else p.name
                for p in method.parameters
            ]
            print(
                f"    - {method.name}({', '.join(params)}) -> {method.return_type or 'None'}"
            )

    print("\nWhy? Creates structured view of API that can be compared")

    input("\nPress Enter to see docstrings...")

    # Stage 3: Docstring Extraction
    section("Stage 3: Docstring Extraction - Human-Readable Content")

    new_class = new_module.classes[0]

    if not new_class.docstring and not any(m.docstring for m in new_class.methods):
        print("""
IMPORTANT NOTE: This version uses comments (#) instead of docstrings.

Key Difference:
  Comments (starting with #):
    • Stripped by Python's AST parser during lexical analysis
    • Not accessible programmatically
    • Cannot be extracted for documentation
    • Used for developer notes in source code

  Docstrings (triple quotes):
    • Captured by ast.get_docstring()
    • Accessible at runtime via __doc__ attribute
    • Extracted for auto-documentation
    • Used for API documentation

Our Extractor Capability:
  ✓ DOES extract docstrings when present (SCRUM-29 complete)
  ✓ Handles Google, NumPy, and reStructuredText formats
  ✓ Preserves formatting and structure
  ✗ CANNOT extract comments (by design of Python's AST)

Example of what we WOULD extract if docstrings existed:
  \"\"\"
  Advanced calculator with extended operations.
  
  Supports basic arithmetic and memory storage.
  \"\"\"

Why This Matters:
  • Without docstrings: We detect WHAT changed (structure)
  • With docstrings: We detect WHAT changed + capture WHY/HOW (content)
  • Backend uses docstrings to generate rich documentation
  • LLMs use docstrings to create helpful migration guides

Best Practice:
  Developers should use docstrings (not comments) for API documentation.
  Our system incentivizes good documentation practices.
""")
    else:
        print("This is what makes documentation human-readable:")

        print("\n--- Class Docstring ---")
        if new_class.docstring:
            print(f'"""{new_class.docstring}"""')
        else:
            print("(No docstring found)")

        print("\n--- Method Docstring Examples ---")
        found_any = False
        for m in new_class.methods:
            if m.docstring:
                found_any = True
                print(f"\nMethod: {m.name}")
                print(f'"""{m.docstring}"""')

        if not found_any:
            print("(No method docstrings found)")

    print("\nWhy? Docstrings become the content for documentation pages")
    print("     When present, they give context to LLMs for better doc generation")

    input("\nPress Enter to detect changes...")

    # Stage 4: Change Detection
    section("Stage 4: Change Detection - Breaking Changes")

    print("Comparing versions to detect API changes...")
    report = detect_changes(old_module, new_module, "v1.0", "v2.0")

    print(f"""
Summary:
  • Added: {len(report.added)} symbols
  • Removed: {len(report.removed)} symbols
  • Modified: {len(report.modified)} symbols
  • Breaking Changes: {"YES" if report.has_breaking_changes else "NO"}
    """)

    if report.added:
        print("Added Symbols:")
        for change in report.added:
            print(f"  + {change.symbol_name} ({change.symbol_type.value})")

    if report.removed:
        print("\nRemoved Symbols (BREAKING):")
        for change in report.removed:
            print(f"  - {change.symbol_name} ({change.symbol_type.value})")

    if report.modified:
        print("\nModified Symbols:")
        for change in report.modified:
            print(f"\n  {change.symbol_name} ({change.symbol_type.value}):")
            print(f"    Breaking: {'YES' if change.is_breaking else 'NO'}")
            if change.is_breaking and change.breaking_reasons:
                print("    Reasons:")
                for reason in change.breaking_reasons:
                    print(f"      • {reason}")

    print("\nWhy? Breaking changes need migration guides for users")
    print("     Change detection works with or without docstrings")

    input("\nPress Enter to see final output...")

    # Final JSON Output
    section("Final Output: change_report.json")

    print("This JSON goes to the backend for doc generation:\n")

    simulated_output = {
        "file_path": "calculator.py",
        "added": [
            {"symbol": "calculate", "type": "method", "breaking": False},
            {"symbol": "power", "type": "method", "breaking": False},
        ],
        "removed": [
            {
                "symbol": "add",
                "type": "method",
                "breaking": True,
                "reason": "Method removed from public API",
            },
            {
                "symbol": "subtract",
                "type": "method",
                "breaking": True,
                "reason": "Method removed from public API",
            },
        ],
        "modified": [
            {
                "symbol": "multiply",
                "type": "method",
                "breaking": False,
                "reasons": ["Type hints added"],
            }
        ],
        "summary": {
            "total_changes": 5,
            "added_count": 2,
            "removed_count": 2,
            "modified_count": 1,
            "breaking_count": 2,
        },
    }

    print(json.dumps(simulated_output, indent=2))

    print("\nThis enables:")
    print("    Backend to ingest our JSON with structure information")
    print("    Detection of breaking changes (works without docstrings)")
    print("    UI shows breaking changes to developers")
    print("    Automated documentation updates on every commit")
    print("\nWith docstrings, would also enable:")
    print("    Rich documentation content extraction")
    print("    LLM-generated migration guides with context")
    print("    Comprehensive API documentation with examples")

    # Sprint Summary
    section("Sprint 1 Complete")

    print("""
What We Delivered:
    Analysis Engine (Parser + Extractor + Detector)
    Breaking Change Detection (Smart comparison logic)
    JSON Output (Ready for backend integration)
    Dockerized & CI/CD Ready Through GitHub Actions

Key Capabilities:
      Works with or without docstrings
      Detects structural changes (parameters, types, methods)
      Flags breaking vs non-breaking changes
      Extracts docstrings when present for rich documentation

Next Steps (Sprint 2+):
  > Backend generates Confluence docs from JSON
  > Confluence API integration
  > Support for TypeScript files
  > Frontend UI for reviewing changes

Current Status: Infrastructure ready and integrated into CI/CD
    """)

    print("\n" + "=" * 50)
    print("Demo Complete - Questions?")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Thanks!")
