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
        # Step 1: Resolve the path (handles relative/absolute/home directory)
        try:
            resolved_path = self._resolve_path(file_path)
        except Exception as e:
            error_msg = f"Failed to resolve path: {e!s}"
            self.logger.error(
                f"Path resolution error for '{file_path}': {error_msg}")
            return ParseResult(
                success=False,
                file_path=file_path,
                error=error_msg,
            )

        # Step 2: Check if file exists
        if not resolved_path.exists():
            error_msg = f"File not found: {resolved_path}"
            self.logger.error(error_msg)
            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error="File not found",
            )

        # Step 3: Check if it's a file (not a directory)
        if not resolved_path.is_file():
            error_msg = f"Path is not a file: {resolved_path}"
            self.logger.error(error_msg)
            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error="Path is not a file",
            )

        # Step 4: Read file contents
        try:
            content = self._read_file_content(resolved_path)
        except UnicodeDecodeError as e:
            error_msg = f"Encoding error: {e!s}"
            self.logger.error(f"Failed to read {resolved_path}: {error_msg}")
            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error=error_msg,
            )
        except OSError as e:
            error_msg = f"IO error: {e!s}"
            self.logger.error(f"Failed to read {resolved_path}: {error_msg}")
            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error=error_msg,
            )

        # Step 5: Parse with ast.parse()
        try:
            tree = ast.parse(
                source=content,
                filename=str(resolved_path),
                type_comments=True,  # Support Python 3.8+ type comments
            )

            # Success! Log and return
            self.logger.info(f"Successfully parsed {resolved_path}")
            return ParseResult(
                success=True,
                file_path=str(resolved_path),
                ast_tree=tree,
            )

        except SyntaxError as e:
            # Extract detailed syntax error information
            error_msg = f"Syntax error: {e.msg}"
            if e.text:
                error_msg += f" | Line content: {e.text.strip()}"

            self.logger.error(
                f"Syntax error in {resolved_path} at line {e.lineno}: {e.msg}",
            )

            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error=error_msg,
                error_line=e.lineno,
            )

        except Exception as e:
            # Catch any other unexpected errors
            error_msg = f"Unexpected error during parsing: {e!s}"
            self.logger.error(f"Failed to parse {resolved_path}: {error_msg}")
            return ParseResult(
                success=False,
                file_path=str(resolved_path),
                error=error_msg,
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
            path = Path(file_path).expanduser()

            # Resolve to absolute path (also resolves symlinks)
            absolute_path = path.resolve()

            return absolute_path
        except Exception as e:
            raise ValueError(f"Invalid path '{file_path}': {e!s}")

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
def parse_python_file(file_path: str, logger: logging.Logger | None = None) -> ParseResult:
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
