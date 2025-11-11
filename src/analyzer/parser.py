import ast
import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseResult:
    """
    Result of parsing a Python file.

    Attributes:
        success: Whether parsing succeeded
        file_path: Path to the file that was parsed
        ast_tree: The parsed AST (None if parsing failed)
        error: Error message if parsing failed
        error_line: Line number where error occurred (for syntax errors)
    """

    success: bool
    file_path: str
    ast_tree: ast.AST | None = None
    error: str | None = None
    error_line: int | None = None


class PythonParser:
    """
    Parser for Python source files using Python's ast module.

    Handles file I/O, syntax errors, and returns structured results
    suitable for downstream static analysis.

    Example:
        >>> parser = PythonParser()
        >>> result = parser.parse("src/main.py")
        >>> if result.success:
        ...     print(f"Parsed {result.file_path} successfully")
        ... else:
        ...     print(f"Error: {result.error}")
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the parser.

        Args:
            logger: Optional logger for diagnostic output. If not provided,
                   creates a logger with the module name.
        """
        self.logger = logger or logging.getLogger(__name__)

    def parse(self, file_path: str) -> ParseResult:
        """
        Parse a Python file and return structured result.

        Handles both relative and absolute paths, gracefully handles
        syntax errors, and logs issues without crashing.

        Supports Python 3.11+ syntax including:
        - Match statements
        - Exception groups
        - Type hints and type comments

        Args:
            file_path: Path to Python file (relative or absolute)

        Returns:
            ParseResult with success status and either AST or error details

        Example:
            >>> parser = PythonParser()
            >>> result = parser.parse("./src/api/main.py")
            >>> if result.success:
            ...     # Access the AST
            ...     tree = result.ast_tree
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
                    except SyntaxError as exc:
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
        """
        Resolve file path to absolute Path object.

        Handles:
        - Relative paths (./src/main.py, src/main.py)
        - Absolute paths (/home/user/project/main.py)
        - Home directory expansion (~/project/main.py)

        Args:
            file_path: Input file path (relative or absolute)

        Returns:
            Resolved absolute Path object

        Raises:
            ValueError: If path is invalid or cannot be resolved
        """
        try:
            # Create Path object and expand ~ if present
            return Path(file_path).expanduser().resolve()
        except Exception as exc:
            raise ValueError(f"Invalid path '{file_path}': {exc!s}") from exc

    def _read_file_content(self, path: Path) -> str:
        """
        Read file contents with proper encoding handling.

        Reads the file as UTF-8 encoded text, which is the standard
        for Python source files.

        Args:
            path: Path object to read

        Returns:
            File contents as string (may be empty for empty files)

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file is not valid UTF-8
            IOError: If file can't be read for other reasons
        """
        # read_text() will raise appropriate exceptions if there are issues
        # We use UTF-8 encoding as it's the standard for Python source files
        return path.read_text(encoding="utf-8")


# Convenience function for simple use cases
def parse_python_file(
    file_path: str, logger: logging.Logger | None = None
) -> ParseResult:
    """
    Convenience function to parse a Python file without creating a parser instance.

    Args:
        file_path: Path to Python file
        logger: Optional logger

    Returns:
        ParseResult object

    Example:
        >>> from analyzer.parser import parse_python_file
        >>> result = parse_python_file("main.py")
        >>> if result.success:
        ...     print("Success!")
    """
    parser = PythonParser(logger=logger)
    return parser.parse(file_path)
