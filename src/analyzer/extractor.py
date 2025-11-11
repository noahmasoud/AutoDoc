import ast
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict


@dataclass
class ParameterInfo:
    """
    Information about a function parameter.

    Attributes:
        name: Parameter name
        annotation: Type annotation as string (e.g., "str", "List[int]")
        default: Default value as string, if any
        kind: Parameter kind (positional, keyword, etc.)
    """
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    kind: str = "positional"  # positional, keyword, *args, **kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)


@dataclass
class FunctionInfo:
    """
    Information about a function or method definition.

    Attributes:
        name: Function name
        parameters: List of parameters
        return_type: Return type annotation as string
        decorators: List of decorator names
        is_async: Whether function is async
        is_public: Whether function is public (no leading underscore)
        is_method: Whether this is a method (inside a class)
        docstring: Function docstring
        lineno: Line number where function is defined
    """
    name: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_public: bool = True
    is_method: bool = False
    docstring: Optional[str] = None
    lineno: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'name': self.name,
            'parameters': [p.to_dict() for p in self.parameters],
            'return_type': self.return_type,
            'decorators': self.decorators,
            'is_async': self.is_async,
            'is_public': self.is_public,
            'is_method': self.is_method,
            'docstring': self.docstring,
            'lineno': self.lineno
        }


@dataclass
class ClassInfo:
    """
    Information about a class definition.

    Attributes:
        name: Class name
        base_classes: List of base class names
        methods: List of methods in the class
        decorators: List of decorator names
        is_public: Whether class is public (no leading underscore)
        docstring: Class docstring
        lineno: Line number where class is defined
    """
    name: str
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_public: bool = True
    docstring: Optional[str] = None
    lineno: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'name': self.name,
            'base_classes': self.base_classes,
            'methods': [m.to_dict() for m in self.methods],
            'decorators': self.decorators,
            'is_public': self.is_public,
            'docstring': self.docstring,
            'lineno': self.lineno
        }


@dataclass
class ModuleInfo:
    """
    Complete information about all symbols in a module.

    Attributes:
        file_path: Path to the source file
        functions: List of module-level functions
        classes: List of classes
        module_docstring: Module-level docstring
    """
    file_path: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    module_docstring: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'file_path': self.file_path,
            'functions': [f.to_dict() for f in self.functions],
            'classes': [c.to_dict() for c in self.classes],
            'module_docstring': self.module_docstring
        }


class SymbolExtractor(ast.NodeVisitor):
    """
    Extracts symbols (functions and classes) from a Python AST.

    Uses the Visitor pattern to walk the AST and extract relevant information
    about functions, classes, and their signatures. Follows OCP - easy to extend
    by adding new visit_* methods.

    Example:
        >>> extractor = SymbolExtractor()
        >>> module_info = extractor.extract(ast_tree, "module.py")
        >>> for func in module_info.functions:
        ...     print(f"Found function: {func.name}")
    """

    def __init__(self):
        """Initialize the extractor."""
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.current_class: Optional[ClassInfo] = None
        self.module_docstring: Optional[str] = None

    def extract(self, tree: ast.AST, file_path: str) -> ModuleInfo:
        """
        Extract all symbols from an AST.

        Args:
            tree: Parsed AST tree
            file_path: Path to the source file

        Returns:
            ModuleInfo containing all extracted symbols
        """
        # Reset state for new extraction
        self.functions = []
        self.classes = []
        self.current_class = None
        self.module_docstring = ast.get_docstring(tree)

        # Visit all nodes in the tree
        self.visit(tree)

        return ModuleInfo(
            file_path=file_path,
            functions=self.functions,
            classes=self.classes,
            module_docstring=self.module_docstring
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit a function definition node.

        Extracts function name, parameters, return type, decorators, and docstring.
        """
        func_info = self._extract_function_info(node, is_async=False)

        if self.current_class:
            # This is a method
            func_info.is_method = True
            self.current_class.methods.append(func_info)
        else:
            # This is a module-level function
            self.functions.append(func_info)

        # Don't visit nested functions (we only want top-level or methods)
        # If you want nested functions, call self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Visit an async function definition node.

        Similar to visit_FunctionDef but marks the function as async.
        """
        func_info = self._extract_function_info(node, is_async=True)

        if self.current_class:
            func_info.is_method = True
            self.current_class.methods.append(func_info)
        else:
            self.functions.append(func_info)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit a class definition node.

        Extracts class name, base classes, decorators, docstring, and methods.
        """
        class_info = ClassInfo(
            name=node.name,
            base_classes=self._extract_base_classes(node),
            decorators=self._extract_decorators(node),
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            lineno=node.lineno
        )

        # Save current class context
        previous_class = self.current_class
        self.current_class = class_info

        # Visit all nodes in the class body (will call visit_FunctionDef for methods)
        self.generic_visit(node)

        # Restore previous context
        self.current_class = previous_class

        # Add to classes list
        self.classes.append(class_info)

    def _extract_function_info(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_async: bool
    ) -> FunctionInfo:
        """
        Extract detailed information from a function node.

        Args:
            node: Function definition node
            is_async: Whether the function is async

        Returns:
            FunctionInfo object with all extracted data
        """
        return FunctionInfo(
            name=node.name,
            parameters=self._extract_parameters(node.args),
            return_type=self._extract_annotation(node.returns),
            decorators=self._extract_decorators(node),
            is_async=is_async,
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            lineno=node.lineno
        )

    def _extract_parameters(self, args: ast.arguments) -> List[ParameterInfo]:
        """
        Extract parameter information from function arguments.

        Args:
            args: Function arguments node

        Returns:
            List of ParameterInfo objects
        """
        parameters = []

        # Regular positional/keyword arguments
        num_defaults = len(args.defaults)
        num_args = len(args.args)

        for i, arg in enumerate(args.args):
            # Skip 'self' and 'cls' parameters
            if arg.arg in ('self', 'cls'):
                continue

            # Determine if this arg has a default value
            default_index = i - (num_args - num_defaults)
            default_value = None
            if default_index >= 0:
                default_value = self._extract_default_value(
                    args.defaults[default_index])

            parameters.append(ParameterInfo(
                name=arg.arg,
                annotation=self._extract_annotation(arg.annotation),
                default=default_value,
                kind="positional"
            ))

        # *args parameter
        if args.vararg:
            parameters.append(ParameterInfo(
                name=args.vararg.arg,
                annotation=self._extract_annotation(args.vararg.annotation),
                kind="*args"
            ))

        # Keyword-only arguments
        num_kw_defaults = len(args.kw_defaults)
        num_kwonlyargs = len(args.kwonlyargs)

        for i, arg in enumerate(args.kwonlyargs):
            default_value = None
            if i < num_kw_defaults and args.kw_defaults[i] is not None:
                default_value = self._extract_default_value(
                    args.kw_defaults[i])

            parameters.append(ParameterInfo(
                name=arg.arg,
                annotation=self._extract_annotation(arg.annotation),
                default=default_value,
                kind="keyword-only"
            ))

        # **kwargs parameter
        if args.kwarg:
            parameters.append(ParameterInfo(
                name=args.kwarg.arg,
                annotation=self._extract_annotation(args.kwarg.annotation),
                kind="**kwargs"
            ))

        return parameters

    def _extract_annotation(self, annotation: Optional[ast.expr]) -> Optional[str]:
        """
        Extract type annotation as a string.

        Args:
            annotation: Annotation expression node

        Returns:
            Annotation as string, or None if no annotation
        """
        if annotation is None:
            return None

        try:
            return ast.unparse(annotation)
        except Exception:
            # Fallback for complex annotations
            return ast.dump(annotation)

    def _extract_default_value(self, default: ast.expr) -> str:
        """
        Extract default value as a string.

        Args:
            default: Default value expression node

        Returns:
            Default value as string
        """
        try:
            return ast.unparse(default)
        except Exception:
            return repr(default)

    def _extract_decorators(self, node: ast.FunctionDef | ast.ClassDef) -> List[str]:
        """
        Extract decorator names from a function or class.

        Args:
            node: Function or class definition node

        Returns:
            List of decorator names as strings
        """
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                decorators.append(ast.dump(decorator))
        return decorators

    def _extract_base_classes(self, node: ast.ClassDef) -> List[str]:
        """
        Extract base class names from a class definition.

        Args:
            node: Class definition node

        Returns:
            List of base class names as strings
        """
        base_classes = []
        for base in node.bases:
            try:
                base_classes.append(ast.unparse(base))
            except Exception:
                base_classes.append(ast.dump(base))
        return base_classes

    def _is_public(self, name: str) -> bool:
        """
        Determine if a symbol is public based on naming convention.

        A symbol is considered public if it doesn't start with an underscore.
        Exception: __init__ and other dunder methods are considered public.

        Args:
            name: Symbol name

        Returns:
            True if symbol is public, False otherwise
        """
        if name.startswith('__') and name.endswith('__'):
            # Dunder methods are public
            return True
        return not name.startswith('_')


# Convenience function
def extract_symbols(tree: ast.AST, file_path: str) -> ModuleInfo:
    """
    Convenience function to extract symbols without creating an extractor instance.

    Args:
        tree: Parsed AST tree
        file_path: Path to the source file

    Returns:
        ModuleInfo containing all extracted symbols

    Example:
        >>> from analyzer.parser import parse_python_file
        >>> from analyzer.extractor import extract_symbols
        >>> result = parse_python_file("module.py")
        >>> if result.success:
        ...     symbols = extract_symbols(result.ast_tree, result.file_path)
    """
    extractor = SymbolExtractor()
    return extractor.extract(tree, file_path)
