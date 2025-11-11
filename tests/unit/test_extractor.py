"""
Tests cover:
- Function extraction (regular and async)
- Class extraction with methods
- Parameter extraction with type hints
- Decorator extraction
- Public vs private symbol identification
- Base class extraction
- Docstring extraction
"""
import ast

import pytest

from src.analyzer.extractor import (
    SymbolExtractor,
    FunctionInfo,
    ClassInfo,
    ParameterInfo,
    ModuleInfo,
    extract_symbols,
)


class TestParameterInfo:
    """Tests for ParameterInfo dataclass"""

    def test_parameter_info_creation(self):
        """Test creating a ParameterInfo object"""
        param = ParameterInfo(
            name="x",
            annotation="int",
            default="0",
            kind="positional",
        )

        assert param.name == "x"
        assert param.annotation == "int"
        assert param.default == "0"
        assert param.kind == "positional"

    def test_parameter_to_dict(self):
        """Test converting ParameterInfo to dict"""
        param = ParameterInfo(name="x", annotation="str")
        param_dict = param.to_dict()

        assert param_dict["name"] == "x"
        assert param_dict["annotation"] == "str"
        assert isinstance(param_dict, dict)


class TestFunctionInfo:
    """Tests for FunctionInfo dataclass"""

    def test_function_info_creation(self):
        """Test creating a FunctionInfo object"""
        func = FunctionInfo(
            name="test_func",
            parameters=[ParameterInfo(name="x", annotation="int")],
            return_type="str",
            decorators=["@staticmethod"],
            is_async=False,
            is_public=True,
        )

        assert func.name == "test_func"
        assert len(func.parameters) == 1
        assert func.return_type == "str"
        assert func.is_public is True

    def test_function_to_dict(self):
        """Test converting FunctionInfo to dict"""
        func = FunctionInfo(
            name="test_func",
            parameters=[ParameterInfo(name="x")],
            return_type="int",
        )
        func_dict = func.to_dict()

        assert func_dict["name"] == "test_func"
        assert len(func_dict["parameters"]) == 1
        assert func_dict["return_type"] == "int"
        assert isinstance(func_dict, dict)


class TestClassInfo:
    """Tests for ClassInfo dataclass"""

    def test_class_info_creation(self):
        """Test creating a ClassInfo object"""
        cls = ClassInfo(
            name="TestClass",
            base_classes=["BaseClass"],
            methods=[FunctionInfo(name="method1")],
            is_public=True,
        )

        assert cls.name == "TestClass"
        assert len(cls.base_classes) == 1
        assert len(cls.methods) == 1
        assert cls.is_public is True

    def test_class_to_dict(self):
        """Test converting ClassInfo to dict"""
        cls = ClassInfo(
            name="TestClass",
            base_classes=["Base"],
            methods=[FunctionInfo(name="method")],
        )
        cls_dict = cls.to_dict()

        assert cls_dict["name"] == "TestClass"
        assert len(cls_dict["base_classes"]) == 1
        assert len(cls_dict["methods"]) == 1
        assert isinstance(cls_dict, dict)


class TestModuleInfo:
    """Tests for ModuleInfo dataclass"""

    def test_module_info_creation(self):
        """Test creating a ModuleInfo object"""
        module = ModuleInfo(
            file_path="test.py",
            functions=[FunctionInfo(name="func1")],
            classes=[ClassInfo(name="Class1")],
        )

        assert module.file_path == "test.py"
        assert len(module.functions) == 1
        assert len(module.classes) == 1

    def test_module_to_dict(self):
        """Test converting ModuleInfo to dict"""
        module = ModuleInfo(
            file_path="test.py",
            functions=[FunctionInfo(name="func")],
            classes=[],
        )
        module_dict = module.to_dict()

        assert module_dict["file_path"] == "test.py"
        assert len(module_dict["functions"]) == 1
        assert isinstance(module_dict, dict)


class TestSymbolExtractor:
    """Tests for SymbolExtractor class"""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance"""
        return SymbolExtractor()

    # ==========================================
    # Tests for function extraction
    # ==========================================

    def test_extract_simple_function(self, extractor):
        """Test extracting a simple function"""
        code = """
def hello():
    return "world"
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "hello"
        assert func.is_public is True
        assert func.is_async is False
        assert len(func.parameters) == 0

    def test_extract_function_with_parameters(self, extractor):
        """Test extracting function with parameters"""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "add"
        assert len(func.parameters) == 2
        assert func.parameters[0].name == "x"
        assert func.parameters[0].annotation == "int"
        assert func.parameters[1].name == "y"
        assert func.return_type == "int"

    def test_extract_function_with_defaults(self, extractor):
        """Test extracting function with default parameters"""
        code = """
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}"
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        func = result.functions[0]
        assert len(func.parameters) == 2
        assert func.parameters[0].default is None
        assert func.parameters[1].default == "'Hello'"

    def test_extract_async_function(self, extractor):
        """Test extracting async function"""
        code = """
async def fetch_data():
    return "data"
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "fetch_data"
        assert func.is_async is True

    def test_extract_function_with_decorators(self, extractor):
        """Test extracting function with decorators"""
        code = """
@staticmethod
@property
def my_func():
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        func = result.functions[0]
        assert len(func.decorators) == 2
        assert "staticmethod" in func.decorators[0]
        assert "property" in func.decorators[1]

    def test_extract_function_with_args_kwargs(self, extractor):
        """Test extracting function with *args and **kwargs"""
        code = """
def func(a, *args, b=None, **kwargs):
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        func = result.functions[0]
        param_names = [p.name for p in func.parameters]
        assert "a" in param_names
        assert "args" in param_names
        assert "b" in param_names
        assert "kwargs" in param_names

        # Check kinds
        param_kinds = {p.name: p.kind for p in func.parameters}
        assert param_kinds["args"] == "*args"
        assert param_kinds["kwargs"] == "**kwargs"

    def test_extract_private_function(self, extractor):
        """Test identifying private functions"""
        code = """
def _private_func():
    pass

def __very_private():
    pass

def public_func():
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.functions) == 3

        private1 = next(
            f for f in result.functions if f.name == "_private_func")
        assert private1.is_public is False

        private2 = next(
            f for f in result.functions if f.name == "__very_private")
        assert private2.is_public is False

        public = next(f for f in result.functions if f.name == "public_func")
        assert public.is_public is True

    def test_extract_function_with_docstring(self, extractor):
        """Test extracting function docstring"""
        code = '''
def documented():
    """This is a docstring"""
    pass
'''
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        func = result.functions[0]
        assert func.docstring == "This is a docstring"

    # ==========================================
    # Tests for class extraction
    # ==========================================

    def test_extract_simple_class(self, extractor):
        """Test extracting a simple class"""
        code = """
class MyClass:
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.name == "MyClass"
        assert cls.is_public is True
        assert len(cls.methods) == 0

    def test_extract_class_with_methods(self, extractor):
        """Test extracting class with methods"""
        code = """
class MyClass:
    def __init__(self):
        pass
    
    def method1(self):
        pass
    
    def method2(self, x: int) -> str:
        return str(x)
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.classes) == 1
        cls = result.classes[0]
        assert len(cls.methods) == 3

        method_names = [m.name for m in cls.methods]
        assert "__init__" in method_names
        assert "method1" in method_names
        assert "method2" in method_names

        # Check that methods are marked as methods
        for method in cls.methods:
            assert method.is_method is True

    def test_extract_class_with_base_classes(self, extractor):
        """Test extracting class with inheritance"""
        code = """
class Parent:
    pass

class Child(Parent):
    pass

class Multi(Parent, object):
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.classes) == 3

        child = next(c for c in result.classes if c.name == "Child")
        assert len(child.base_classes) == 1
        assert "Parent" in child.base_classes[0]

        multi = next(c for c in result.classes if c.name == "Multi")
        assert len(multi.base_classes) == 2

    def test_extract_class_with_decorators(self, extractor):
        """Test extracting class with decorators"""
        code = """
@dataclass
@frozen
class MyClass:
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        cls = result.classes[0]
        assert len(cls.decorators) == 2
        assert "dataclass" in cls.decorators[0]
        assert "frozen" in cls.decorators[1]

    def test_extract_private_class(self, extractor):
        """Test identifying private classes"""
        code = """
class _PrivateClass:
    pass

class PublicClass:
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        private = next(c for c in result.classes if c.name == "_PrivateClass")
        assert private.is_public is False

        public = next(c for c in result.classes if c.name == "PublicClass")
        assert public.is_public is True

    def test_extract_class_with_docstring(self, extractor):
        """Test extracting class docstring"""
        code = '''
class Documented:
    """This is a class docstring"""
    pass
'''
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        cls = result.classes[0]
        assert cls.docstring == "This is a class docstring"

    def test_methods_exclude_self_parameter(self, extractor):
        """Test that 'self' parameter is excluded from methods"""
        code = """
class MyClass:
    def method(self, x: int):
        pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        method = result.classes[0].methods[0]
        param_names = [p.name for p in method.parameters]
        assert "self" not in param_names
        assert "x" in param_names

    def test_class_methods_exclude_cls_parameter(self, extractor):
        """Test that 'cls' parameter is excluded from class methods"""
        code = """
class MyClass:
    @classmethod
    def create(cls, x: int):
        pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        method = result.classes[0].methods[0]
        param_names = [p.name for p in method.parameters]
        assert "cls" not in param_names
        assert "x" in param_names

    # ==========================================
    # Tests for module-level extraction
    # ==========================================

    def test_extract_module_docstring(self, extractor):
        """Test extracting module-level docstring"""
        code = '''"""This is a module docstring"""

def func():
    pass
'''
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert result.module_docstring == "This is a module docstring"

    def test_extract_mixed_symbols(self, extractor):
        """Test extracting both functions and classes"""
        code = """
def func1():
    pass

class Class1:
    def method1(self):
        pass

def func2():
    pass

class Class2:
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert len(result.functions) == 2
        assert len(result.classes) == 2
        assert result.functions[0].name == "func1"
        assert result.functions[1].name == "func2"
        assert result.classes[0].name == "Class1"
        assert result.classes[1].name == "Class2"

    def test_extract_preserves_order(self, extractor):
        """Test that extraction preserves definition order"""
        code = """
def first():
    pass

def second():
    pass

def third():
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        assert result.functions[0].name == "first"
        assert result.functions[1].name == "second"
        assert result.functions[2].name == "third"

    # ==========================================
    # Tests for special cases
    # ==========================================

    def test_extract_dunder_methods_are_public(self, extractor):
        """Test that dunder methods are considered public"""
        code = """
class MyClass:
    def __init__(self):
        pass
    
    def __str__(self):
        pass
    
    def _private(self):
        pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        methods = result.classes[0].methods
        init = next(m for m in methods if m.name == "__init__")
        str_method = next(m for m in methods if m.name == "__str__")
        private = next(m for m in methods if m.name == "_private")

        assert init.is_public is True
        assert str_method.is_public is True
        assert private.is_public is False

    def test_extract_complex_type_annotations(self, extractor):
        """Test extracting complex type annotations"""
        code = """
from typing import List, Dict, Optional

def func(
    items: List[Dict[str, int]],
    config: Optional[Dict[str, str]] = None
) -> List[str]:
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        func = result.functions[0]
        assert "List" in func.parameters[0].annotation
        assert "Dict" in func.parameters[0].annotation
        assert "Optional" in func.parameters[1].annotation
        assert "List[str]" in func.return_type

    def test_extract_nested_classes_are_extracted(self, extractor):
        """Test that nested classes are extracted"""
        code = """
class Outer:
    class Inner:
        pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        # Both Outer and Inner are extracted
        assert len(result.classes) == 2
        class_names = [c.name for c in result.classes]
        assert "Outer" in class_names
        assert "Inner" in class_names

    def test_line_numbers_extracted(self, extractor):
        """Test that line numbers are extracted correctly"""
        code = """
def func1():
    pass

class MyClass:
    pass

def func2():
    pass
"""
        tree = ast.parse(code)
        result = extractor.extract(tree, "test.py")

        # Line numbers should be present
        assert result.functions[0].lineno > 0
        assert result.classes[0].lineno > 0
        assert result.functions[1].lineno > result.classes[0].lineno


class TestConvenienceFunction:
    """Tests for extract_symbols convenience function"""

    def test_extract_symbols_function(self):
        """Test the convenience function"""
        code = """
def hello():
    return "world"
"""
        tree = ast.parse(code)
        result = extract_symbols(tree, "test.py")

        assert isinstance(result, ModuleInfo)
        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"


class TestJSONSerialization:
    """Tests for JSON serialization"""

    def test_module_info_to_dict_is_json_serializable(self):
        """Test that ModuleInfo.to_dict() produces JSON-serializable output"""
        import json

        code = """
def func(x: int) -> str:
    '''A function'''
    return str(x)

class MyClass:
    '''A class'''
    def method(self, y: int):
        pass
"""
        tree = ast.parse(code)
        extractor = SymbolExtractor()
        result = extractor.extract(tree, "test.py")

        # Convert to dict
        result_dict = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["file_path"] == "test.py"
        assert len(parsed["functions"]) == 1
        assert len(parsed["classes"]) == 1
