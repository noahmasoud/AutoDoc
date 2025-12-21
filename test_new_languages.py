#!/usr/bin/env python3
"""
Dry run test script for JavaScript and Go language support.

This script tests the new JavaScript and Go analyzers without requiring
a full CI/CD run or database setup.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_javascript_parser():
    """Test JavaScript parser."""
    print("=" * 60)
    print("Testing JavaScript Parser")
    print("=" * 60)
    
    try:
        from services.javascript_parser import JavaScriptParser
        
        # Create a test JavaScript file
        test_file = project_root / "test_dry_run.js"
        test_file.write_text("""
/**
 * Test JavaScript file for dry run
 */

// Function declaration
function calculateSum(a, b) {
    return a + b;
}

// Arrow function
const multiply = (x, y) => x * y;

// Class declaration
class Calculator {
    constructor() {
        this.value = 0;
    }
    
    add(n) {
        this.value += n;
        return this.value;
    }
}

// Export
export { calculateSum, Calculator };
""")
        
        print(f"✓ Created test file: {test_file}")
        
        try:
            parser = JavaScriptParser()
            print("✓ JavaScriptParser initialized")
            
            # Try to parse the file
            ast = parser.parse_file(str(test_file))
            print("✓ JavaScript file parsed successfully")
            
            # Extract symbols
            symbols = parser.extract_public_symbols(ast)
            print(f"✓ Extracted symbols:")
            print(f"  - Functions: {len(symbols.get('functions', []))}")
            print(f"  - Classes: {len(symbols.get('classes', []))}")
            
            for func in symbols.get('functions', []):
                print(f"    • {func.get('name', 'unknown')} (line {func.get('line', '?')})")
            
            for cls in symbols.get('classes', []):
                print(f"    • {cls.get('name', 'unknown')} (line {cls.get('line', '?')})")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                print(f"✓ Cleaned up test file")
                
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_javascript_analyzer():
    """Test JavaScript analyzer."""
    print("\n" + "=" * 60)
    print("Testing JavaScript Analyzer")
    print("=" * 60)
    
    try:
        from services.javascript_analyzer import JavaScriptAnalyzer
        
        # Create test files
        test_files = []
        for i, content in enumerate([
            "function test1() { return 1; }",
            "class TestClass { method() {} }",
            "const arrow = () => {};"
        ]):
            test_file = project_root / f"test_js_{i}.js"
            test_file.write_text(content)
            test_files.append(str(test_file))
        
        print(f"✓ Created {len(test_files)} test files")
        
        try:
            analyzer = JavaScriptAnalyzer()
            print("✓ JavaScriptAnalyzer initialized")
            
            # Analyze files
            result = analyzer.analyze_changed_files(test_files, "dry_run_001")
            
            print(f"✓ Analysis complete:")
            print(f"  - Files processed: {result['files_processed']}")
            print(f"  - Files failed: {result['files_failed']}")
            print(f"  - Symbols extracted:")
            for symbol_type, count in result['symbols_extracted'].items():
                if count > 0:
                    print(f"    • {symbol_type}: {count}")
            
            return result['files_processed'] > 0
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            for test_file in test_files:
                if Path(test_file).exists():
                    Path(test_file).unlink()
            print(f"✓ Cleaned up test files")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_go_parser_mock():
    """Test Go parser (mocked since Go may not be installed)."""
    print("\n" + "=" * 60)
    print("Testing Go Parser (Mocked)")
    print("=" * 60)
    
    try:
        from services.go_parser import GoParser, GoNotFoundError
        
        # Check if Go is available
        import subprocess
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            go_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            go_available = False
        
        if not go_available:
            print("⚠ Go compiler not found - skipping Go parser test")
            print("  (This is expected if Go is not installed)")
            return True  # Not a failure, just not available
        
        # Try to compile the Go parser
        go_script = project_root / "scripts" / "parse-go.go"
        if not go_script.exists():
            print(f"✗ Go parser script not found: {go_script}")
            return False
        
        print(f"✓ Found Go parser script: {go_script}")
        
        try:
            parser = GoParser()
            print("✓ GoParser initialized")
            
            # Create a test Go file
            test_file = project_root / "test_dry_run.go"
            test_file.write_text("""
package main

import "fmt"

// TestFunction is a test function
func TestFunction(param string) string {
    return fmt.Sprintf("Hello, %s", param)
}

// TestType is a test type
type TestType struct {
    Name  string
    Value int
}

func main() {
    fmt.Println("Hello, World!")
}
""")
            
            print(f"✓ Created test file: {test_file}")
            
            # Try to parse the file
            ast = parser.parse_file(str(test_file))
            print("✓ Go file parsed successfully")
            
            # Extract symbols
            symbols = parser.extract_public_symbols(ast)
            print(f"✓ Extracted symbols:")
            for symbol_type, symbol_list in symbols.items():
                if symbol_list:
                    print(f"  - {symbol_type}: {len(symbol_list)}")
                    for sym in symbol_list[:3]:  # Show first 3
                        print(f"    • {sym.get('name', 'unknown')} (line {sym.get('line', '?')})")
            
            return True
            
        except GoNotFoundError:
            print("⚠ Go compiler not found - skipping Go parser test")
            return True  # Not a failure
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                print(f"✓ Cleaned up test file")
                
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_database_models():
    """Test that database models can be imported."""
    print("\n" + "=" * 60)
    print("Testing Database Models")
    print("=" * 60)
    
    try:
        from db.models import JavaScriptSymbol, GoSymbol
        
        print("✓ JavaScriptSymbol model imported")
        print("✓ GoSymbol model imported")
        
        # Check model attributes
        assert hasattr(JavaScriptSymbol, 'symbol_name')
        assert hasattr(JavaScriptSymbol, 'symbol_type')
        assert hasattr(GoSymbol, 'symbol_name')
        assert hasattr(GoSymbol, 'symbol_type')
        
        print("✓ Model attributes verified")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"✗ Model verification failed: {e}")
        return False


def main():
    """Run all dry run tests."""
    print("\n" + "=" * 60)
    print("AutoDoc JavaScript & Go Language Support - Dry Run Test")
    print("=" * 60)
    print()
    
    results = {
        "JavaScript Parser": test_javascript_parser(),
        "JavaScript Analyzer": test_javascript_analyzer(),
        "Go Parser": test_go_parser_mock(),
        "Database Models": test_database_models(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

