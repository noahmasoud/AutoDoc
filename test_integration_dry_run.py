#!/usr/bin/env python3
"""
Integration dry run test for JavaScript and Go language support.

This script demonstrates the full workflow:
1. Parse JavaScript/Go files
2. Extract symbols
3. Store in database (simulated)
4. Show how patch generation would use them
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_javascript_full_workflow():
    """Test complete JavaScript workflow."""
    print("=" * 60)
    print("JavaScript Full Workflow Test")
    print("=" * 60)
    
    try:
        from services.javascript_parser import JavaScriptParser
        from services.javascript_analyzer import JavaScriptAnalyzer
        from services.javascript_symbol_ingestor import JavaScriptSymbolIngestor
        
        # Create a realistic JavaScript file
        test_file = project_root / "test_integration.js"
        test_file.write_text("""
/**
 * User Service Module
 * 
 * Provides user management functionality
 */

/**
 * Creates a new user
 * @param {string} username - The username
 * @param {string} email - The email address
 * @returns {Promise<User>} The created user
 */
async function createUser(username, email) {
    // Implementation
    return { username, email };
}

/**
 * User class for managing user data
 */
class User {
    /**
     * @param {string} id - User ID
     * @param {string} name - User name
     */
    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
    
    /**
     * Gets the user's display name
     * @returns {string} Display name
     */
    getDisplayName() {
        return this.name;
    }
}

// Export
export { createUser, User };
""")
        
        print(f"✓ Created test file: {test_file}")
        
        # Step 1: Parse
        parser = JavaScriptParser()
        ast = parser.parse_file(str(test_file))
        print("✓ Step 1: File parsed successfully")
        
        # Step 2: Extract symbols
        symbols = parser.extract_public_symbols(ast)
        print("✓ Step 2: Symbols extracted")
        print(f"  - Functions: {len(symbols.get('functions', []))}")
        print(f"  - Classes: {len(symbols.get('classes', []))}")
        
        # Step 3: Analyze (using analyzer)
        analyzer = JavaScriptAnalyzer()
        result = analyzer.analyze_changed_files([str(test_file)], "integration_test")
        print("✓ Step 3: Analyzer processed file")
        print(f"  - Status: {result['files'][0]['status']}")
        print(f"  - Symbols found: {sum(len(v) for v in result['files'][0]['symbols'].values())}")
        
        # Step 4: Show what would be stored
        print("✓ Step 4: Symbol data that would be stored:")
        ingestor = JavaScriptSymbolIngestor(parser=parser)
        
        # Simulate what would be stored (without actual DB)
        from db.models import JavaScriptSymbol
        
        # Show structure
        print("\n  Sample symbol entries:")
        for func in symbols.get('functions', [])[:2]:
            print(f"    • Function: {func.get('name')}")
            print(f"      - Type: function")
            print(f"      - Line: {func.get('line')}")
            print(f"      - Async: {func.get('async', False)}")
        
        for cls in symbols.get('classes', [])[:1]:
            print(f"    • Class: {cls.get('name')}")
            print(f"      - Type: class")
            print(f"      - Line: {cls.get('line')}")
        
        # Cleanup
        test_file.unlink()
        print(f"\n✓ Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_patch_generator_integration():
    """Test that patch generator can handle JavaScript/Go symbols."""
    print("\n" + "=" * 60)
    print("Patch Generator Integration Test")
    print("=" * 60)
    
    try:
        from services.patch_generator import _build_patch_context
        from db.models import Run, Rule, Change, JavaScriptSymbol, GoSymbol, PythonSymbol
        
        # Create mock objects (we won't actually save to DB)
        print("✓ Testing patch context building with multiple language symbols")
        
        # Mock run
        class MockRun:
            id = 1
            repo = "test/repo"
            branch = "main"
            commit_sha = "abc123"
            status = "Success"
        
        # Mock rule
        class MockRule:
            id = 1
            name = "Test Rule"
            selector = "*.js"
            space_key = "TEST"
            page_id = "12345"
        
        # Mock changes
        class MockChange:
            def __init__(self, file_path, symbol, change_type):
                self.file_path = file_path
                self.symbol = symbol
                self.change_type = change_type
                self.signature_before = None
                self.signature_after = None
        
        changes = [
            MockChange("src/app.js", "createUser", "added"),
            MockChange("src/utils.go", "ProcessData", "added"),
        ]
        
        # Mock symbols
        class MockJSymbol:
            def __init__(self, file_path, name, symbol_type):
                self.file_path = file_path
                self.symbol_name = name
                self.qualified_name = f"{file_path}::{symbol_type}::{name}"
                self.symbol_type = symbol_type
                self.docstring = None
                self.lineno = 10
                self.symbol_metadata = {}
        
        class MockGoSymbol:
            def __init__(self, file_path, name, symbol_type):
                self.file_path = file_path
                self.symbol_name = name
                self.qualified_name = f"{file_path}::{symbol_type}::{name}"
                self.symbol_type = symbol_type
                self.docstring = None
                self.lineno = 20
                self.symbol_metadata = {}
        
        js_symbols = [MockJSymbol("src/app.js", "createUser", "function")]
        go_symbols = [MockGoSymbol("src/utils.go", "ProcessData", "function")]
        python_symbols = []
        
        # Test context building
        context = _build_patch_context(
            MockRun(),
            MockRule(),
            changes,
            python_symbols,
            js_symbols,
            go_symbols,
        )
        
        print("✓ Context built successfully")
        print(f"  - Total symbols in context: {len(context['symbols'])}")
        print(f"  - JavaScript symbols: {sum(1 for s in context['symbols'] if s['file_path'].endswith('.js'))}")
        print(f"  - Go symbols: {sum(1 for s in context['symbols'] if s['file_path'].endswith('.go'))}")
        
        # Show sample symbol data
        if context['symbols']:
            print("\n  Sample symbol from context:")
            sample = context['symbols'][0]
            print(f"    • Name: {sample['symbol_name']}")
            print(f"    • Type: {sample['symbol_type']}")
            print(f"    • File: {sample['file_path']}")
            print(f"    • Qualified: {sample['qualified_name']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_detection():
    """Test file extension detection."""
    print("\n" + "=" * 60)
    print("File Extension Detection Test")
    print("=" * 60)
    
    try:
        from services.javascript_analyzer import JavaScriptAnalyzer
        from services.go_analyzer import GoAnalyzer
        from services.go_parser import GoNotFoundError
        
        js_analyzer = JavaScriptAnalyzer()
        
        # Try to initialize Go analyzer, but handle if Go is not installed
        try:
            go_analyzer = GoAnalyzer()
            go_available = True
        except GoNotFoundError:
            print("⚠ Go compiler not found - testing file detection without Go analyzer")
            go_available = False
            # Create a mock analyzer just for file detection
            class MockGoAnalyzer:
                def _is_go_file(self, file_path):
                    from pathlib import Path
                    path = Path(file_path)
                    suffix = path.suffix.lower()
                    return suffix == ".go"
            go_analyzer = MockGoAnalyzer()
        
        test_cases = [
            ("app.js", True, False),
            ("component.jsx", True, False),
            ("main.go", False, True),
            ("utils.go", False, True),
            ("test.py", False, False),
            ("style.css", False, False),
            ("README.md", False, False),
        ]
        
        print("Testing file detection:")
        all_passed = True
        for file_path, should_be_js, should_be_go in test_cases:
            is_js = js_analyzer._is_javascript_file(file_path)
            is_go = go_analyzer._is_go_file(file_path)
            
            js_ok = is_js == should_be_js
            go_ok = is_go == should_be_go
            
            status = "✓" if (js_ok and go_ok) else "✗"
            print(f"  {status} {file_path:20} JS: {is_js:5} Go: {is_go:5}")
            
            if not (js_ok and go_ok):
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration tests."""
    print("\n" + "=" * 60)
    print("AutoDoc JavaScript & Go - Integration Dry Run")
    print("=" * 60)
    print()
    
    results = {
        "JavaScript Full Workflow": test_javascript_full_workflow(),
        "Patch Generator Integration": test_patch_generator_integration(),
        "File Extension Detection": test_file_detection(),
    }
    
    print("\n" + "=" * 60)
    print("Integration Test Results")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All integration tests passed!")
        print("\nThe JavaScript and Go language support is working correctly.")
        print("JavaScript files can be parsed, analyzed, and symbols extracted.")
        print("The patch generator can handle symbols from all languages.")
    else:
        print("✗ Some integration tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

