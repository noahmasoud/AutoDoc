import ast
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Union


@dataclass
class ParameterInfo:
    # function parameter(s)

    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    kind: str = "positional"  # positional, keyword, *args, **kwargs

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FunctionInfo:
    # function or method definition.
    name: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_public: bool = True
    is_method: bool = False
    docstring: Optional[str] = None
    lineno: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "decorators": self.decorators,
            "is_async": self.is_async,
            "is_public": self.is_public,
            "is_method": self.is_method,
            "docstring": self.docstring,
            "lineno": self.lineno,
        }


@dataclass
class ClassInfo:
    # class definition.
    name: str
    base_classes: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    is_public: bool = True
    docstring: Optional[str] = None
    lineno: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "base_classes": self.base_classes,
            "methods": [m.to_dict() for m in self.methods],
            "decorators": self.decorators,
            "is_public": self.is_public,
            "docstring": self.docstring,
            "lineno": self.lineno,
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
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    module_docstring: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "module_docstring": self.module_docstring,
        }

    # extract the symbols (functions and classes) from an AST
    # use the visitor pattern to walk the AST and extract relevant information


class SymbolExtractor(ast.NodeVisitor):
    def __init__(self):
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.current_class: Optional[ClassInfo] = None
        self.module_docstring: Optional[str] = None

    def extract(self, tree: ast.AST, file_path: str) -> ModuleInfo:
        # extract all symbols from an AST
        if not isinstance(tree, ast.Module):
            raise TypeError("SymbolExtractor.extract expects an ast.Module instance")

        module_tree = tree

        # rese state for new extraction
        self.functions = []
        self.classes = []
        self.current_class = None
        self.module_docstring = ast.get_docstring(module_tree)

        # visit all nodes in the tree
        self.visit(module_tree)

        return ModuleInfo(
            file_path=file_path,
            functions=self.functions,
            classes=self.classes,
            module_docstring=self.module_docstring,
        )

    # vistit a function definition node.
    # extract function name, parameters, return type, decorators, and docstring.
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        func_info = self._extract_function_info(node, is_async=False)

        if self.current_class:
            func_info.is_method = True
            self.current_class.methods.append(func_info)
        else:
            self.functions.append(func_info)

        # do not visit nested functions. we only want top-level or methods

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        func_info = self._extract_function_info(node, is_async=True)

        if self.current_class:
            func_info.is_method = True
            self.current_class.methods.append(func_info)
        else:
            self.functions.append(func_info)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_info = ClassInfo(
            name=node.name,
            base_classes=self._extract_base_classes(node),
            decorators=self._extract_decorators(node),
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            lineno=node.lineno,
        )

        # save current class context
        previous_class = self.current_class
        self.current_class = class_info

        # visit all nodes in the class body
        self.generic_visit(node)

        # restore previous context
        self.current_class = previous_class

        self.classes.append(class_info)

    # Extract detailed information from a function node.
    def _extract_function_info(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool
    ) -> FunctionInfo:
        return FunctionInfo(
            name=node.name,
            parameters=self._extract_parameters(node.args),
            return_type=self._extract_annotation(node.returns),
            decorators=self._extract_decorators(node),
            is_async=is_async,
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            lineno=node.lineno,
        )

    def _extract_parameters(self, args: ast.arguments) -> list[ParameterInfo]:
        parameters = []

        # reg positional/keyword arguments
        num_defaults = len(args.defaults)
        num_args = len(args.args)

        for i, arg in enumerate(args.args):
            # do not account for 'self' and 'cls' parameters
            if arg.arg in ("self", "cls"):
                continue

            # if this arg has a default value
            default_index = i - (num_args - num_defaults)
            default_value = None
            if default_index >= 0:
                default_value = self._extract_default_value(
                    args.defaults[default_index]
                )

            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    annotation=self._extract_annotation(arg.annotation),
                    default=default_value,
                    kind="positional",
                )
            )

        # *args parameter
        if args.vararg:
            parameters.append(
                ParameterInfo(
                    name=args.vararg.arg,
                    annotation=self._extract_annotation(args.vararg.annotation),
                    kind="*args",
                )
            )

        # only take keyword-only arguments
        num_kw_defaults = len(args.kw_defaults)

        for i, arg in enumerate(args.kwonlyargs):
            default_value = None
            if i < num_kw_defaults and args.kw_defaults[i] is not None:
                default_value = self._extract_default_value(args.kw_defaults[i])

            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    annotation=self._extract_annotation(arg.annotation),
                    default=default_value,
                    kind="keyword-only",
                )
            )

        # **kwargs parameter
        if args.kwarg:
            parameters.append(
                ParameterInfo(
                    name=args.kwarg.arg,
                    annotation=self._extract_annotation(args.kwarg.annotation),
                    kind="**kwargs",
                )
            )

        return parameters

    def _extract_annotation(self, annotation: Optional[ast.expr]) -> Optional[str]:
        if annotation is None:
            return None

        try:
            return ast.unparse(annotation)
        except Exception:
            # Fallback for complex annotations
            return ast.dump(annotation)

    def _extract_default_value(self, default: Optional[ast.expr]) -> str:
        if default is None:
            return "None"

        try:
            return ast.unparse(default)
        except Exception:
            return repr(default)

    # extract decorator names from a function or class.
    def _extract_decorators(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    ) -> list[str]:
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                decorators.append(ast.dump(decorator))
        return decorators

    def _extract_base_classes(self, node: ast.ClassDef) -> list[str]:
        base_classes = []
        for base in node.bases:
            try:
                base_classes.append(ast.unparse(base))
            except Exception:
                base_classes.append(ast.dump(base))
        return base_classes

    def _is_public(self, name: str) -> bool:
        if name.startswith("__") and name.endswith("__"):
            return True
        return not name.startswith("_")


# convenience function
def extract_symbols(tree: ast.AST, file_path: str) -> ModuleInfo:
    extractor = SymbolExtractor()
    return extractor.extract(tree, file_path)
