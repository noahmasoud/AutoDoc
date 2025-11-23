import ast
import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseResult:
    success: bool
    file_path: str
    ast_tree: ast.AST | None = None
    error: str | None = None
    error_line: int | None = None


# parser for Python source files using Python's ast module.


class PythonParser:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, file_path: str) -> ParseResult:
        """
        Parse a Python file and return structured result.

        Handles both relative and absolute paths, gracefully handles
        syntax errors, and logs issues without crashing.
        """
        success = False
        resolved_path_str = file_path
        ast_tree: ast.AST | None = None
        error_msg: str | None = None
        error_line: int | None = None

        resolved_path: Path | None = None
        try:
            resolved_path = self._resolve_path(file_path)
        except Exception as exc:
            error_msg = f"Failed to resolve path: {exc!s}"
            self.logger.exception(
                "Path resolution error for '%s': %s",
                file_path,
                error_msg,
            )

        if resolved_path is not None and error_msg is None:
            resolved_path_str = str(resolved_path)

            if not resolved_path.exists():
                error_msg = f"File not found: {resolved_path}"
                self.logger.exception(error_msg)
            elif not resolved_path.is_file():
                error_msg = f"Path is not a file: {resolved_path}"
                self.logger.exception(error_msg)
            else:
                try:
                    content = self._read_file_content(resolved_path)
                except UnicodeDecodeError as exc:
                    error_msg = f"Encoding error: {exc!s}"
                    self.logger.exception(
                        "Failed to read %s: %s",
                        resolved_path,
                        error_msg,
                    )
                except OSError as exc:
                    error_msg = f"IO error: {exc!s}"
                    self.logger.exception(
                        "Failed to read %s: %s",
                        resolved_path,
                        error_msg,
                    )
                else:
                    try:
                        ast_tree = ast.parse(
                            source=content,
                            filename=resolved_path_str,
                            type_comments=True,
                        )
                    except SyntaxError as exc:  # def
                        error_msg = f"Syntax error: {exc.msg}"
                        if exc.text:
                            error_msg += f" | Line content: {exc.text.strip()}"
                        error_line = exc.lineno
                        self.logger.exception(
                            "Syntax error in %s at line %s: %s",
                            resolved_path,
                            exc.lineno,
                            exc.msg,
                        )
                    except Exception as exc:
                        error_msg = f"Unexpected error during parsing: {exc!s}"
                        self.logger.exception(
                            "Failed to parse %s: %s",
                            resolved_path,
                            error_msg,
                        )
                    else:
                        success = True
                        self.logger.info("Successfully parsed %s", resolved_path)

        return ParseResult(
            success=success,
            file_path=resolved_path_str,
            ast_tree=ast_tree,
            error=error_msg,
            error_line=error_line,
        )

    def _resolve_path(self, file_path: str) -> Path:
        try:
            # Create Path object and expand ~ if present
            return Path(file_path).expanduser().resolve()
        except Exception as exc:
            raise ValueError(f"Invalid path '{file_path}': {exc!s}") from exc

    def _read_file_content(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")


#  function for simple use cases
def parse_python_file(
    file_path: str, logger: logging.Logger | None = None
) -> ParseResult:
    parser = PythonParser(logger=logger)
    return parser.parse(file_path)


def parse_python_code(code: str, filename: str = "<string>") -> ast.Module:
    """
    Parse Python source code string and return its AST.

    Simple wrapper for ast.parse() for testing and inline code.

    Args:
        code: Python source code as string
        filename: Optional filename for error messages

    Returns:
        ast.Module object

    Raises:
        SyntaxError: If code has syntax errors
    """
    return ast.parse(code, filename=filename, type_comments=True)
