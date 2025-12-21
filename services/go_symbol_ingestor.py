"""Service for persisting extracted Go symbol metadata."""

from __future__ import annotations

from pathlib import Path
import typing as t
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as SQLASession
else:
    SQLASession = Any

from db.models import GoSymbol
from services.go_parser import GoParser


class GoSymbolIngestor:
    """Extract Go symbols and persist them with godoc comments."""

    def __init__(
        self,
        parser: GoParser | None = None,
    ) -> None:
        self._parser = parser or GoParser()

    def ingest_files(
        self,
        run_id: int,
        go_files: t.Sequence[str],
        db: SQLASession,
    ) -> list[GoSymbol]:
        """Parse, extract, and persist symbols for the provided files."""
        persisted: list[GoSymbol] = []
        for file_path in go_files:
            persisted.extend(self._ingest_single_file(run_id, file_path, db))
        return persisted

    def _ingest_single_file(
        self,
        run_id: int,
        file_path: str,
        db: SQLASession,
    ) -> list[GoSymbol]:
        try:
            ast = self._parser.parse_file(file_path)
            symbols_dict = self._parser.extract_public_symbols(ast)
        except Exception:
            # If parsing fails, return empty list
            return []

        self._delete_existing_symbols(run_id, file_path, db)

        symbol_entries = list(self._flatten_symbols(file_path, symbols_dict, ast))

        persisted: list[GoSymbol] = []
        for entry in symbol_entries:
            symbol = GoSymbol(
                run_id=run_id,
                file_path=entry["file_path"],
                symbol_name=entry["symbol_name"],
                qualified_name=entry["qualified_name"],
                symbol_type=entry["symbol_type"],
                docstring=entry["docstring"],
                lineno=entry["lineno"],
                symbol_metadata=entry["symbol_metadata"],
            )
            db.add(symbol)
            persisted.append(symbol)

        db.flush()
        return persisted

    @staticmethod
    def _delete_existing_symbols(
        run_id: int,
        file_path: str,
        db: SQLASession,
    ) -> None:
        existing_symbols = (
            db.query(GoSymbol)
            .filter(
                GoSymbol.run_id == run_id,
                GoSymbol.file_path == file_path,
            )
            .all()
        )

        if not existing_symbols:
            return

        for symbol in existing_symbols:
            db.delete(symbol)

        db.flush()

        if db.is_active:
            from sqlalchemy.exc import InvalidRequestError

            for symbol in existing_symbols:
                try:
                    db.expunge(symbol)
                except InvalidRequestError:
                    continue

    def _flatten_symbols(
        self,
        file_path: str,
        symbols_dict: dict[str, list[dict[str, Any]]],
        ast: dict[str, Any],
    ) -> t.Iterable[dict]:
        module_path = self._normalize_path(file_path)

        # Package-level entry
        package_name = ast.get("package", "main")
        yield {
            "file_path": file_path,
            "symbol_name": package_name,
            "qualified_name": self._build_package_qualified_name(file_path, package_name),
            "symbol_type": "package",
            "docstring": None,
            "lineno": 1,
            "symbol_metadata": {"package": package_name},
        }

        # Process functions (including methods)
        for func in symbols_dict.get("functions", []):
            yield self._build_function_entry(file_path, module_path, func)

        # Process types
        for type_def in symbols_dict.get("types", []):
            yield self._build_type_entry(file_path, module_path, type_def)

        # Process interfaces
        for interface in symbols_dict.get("interfaces", []):
            yield self._build_interface_entry(file_path, module_path, interface)

        # Process structs
        for struct in symbols_dict.get("structs", []):
            yield self._build_struct_entry(file_path, module_path, struct)

        # Process constants
        for const in symbols_dict.get("consts", []):
            yield self._build_const_entry(file_path, module_path, const)

        # Process variables
        for var in symbols_dict.get("vars", []):
            yield self._build_var_entry(file_path, module_path, var)

    @staticmethod
    def _normalize_path(file_path: str) -> Path:
        try:
            return Path(file_path).resolve()
        except RuntimeError:
            return Path(file_path)

    def _build_function_entry(
        self,
        file_path: str,
        module_path: Path,
        func: dict[str, Any],
    ) -> dict:
        name = func.get("name", "")
        lineno = func.get("line")
        is_method = func.get("is_method", False)
        symbol_type = "method" if is_method else "function"
        qualified_name = self._build_qualified_name(
            module_path,
            parts=(symbol_type, name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": symbol_type,
            "docstring": func.get("doc"),
            "lineno": lineno,
            "symbol_metadata": func,
        }

    def _build_type_entry(
        self,
        file_path: str,
        module_path: Path,
        type_def: dict[str, Any],
    ) -> dict:
        name = type_def.get("name", "")
        lineno = type_def.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("type", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "type",
            "docstring": type_def.get("doc"),
            "lineno": lineno,
            "symbol_metadata": type_def,
        }

    def _build_interface_entry(
        self,
        file_path: str,
        module_path: Path,
        interface: dict[str, Any],
    ) -> dict:
        name = interface.get("name", "")
        lineno = interface.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("interface", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "interface",
            "docstring": interface.get("doc"),
            "lineno": lineno,
            "symbol_metadata": interface,
        }

    def _build_struct_entry(
        self,
        file_path: str,
        module_path: Path,
        struct: dict[str, Any],
    ) -> dict:
        name = struct.get("name", "")
        lineno = struct.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("struct", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "struct",
            "docstring": struct.get("doc"),
            "lineno": lineno,
            "symbol_metadata": struct,
        }

    def _build_const_entry(
        self,
        file_path: str,
        module_path: Path,
        const: dict[str, Any],
    ) -> dict:
        name = const.get("name", "")
        lineno = const.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("const", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "const",
            "docstring": const.get("doc"),
            "lineno": lineno,
            "symbol_metadata": const,
        }

    def _build_var_entry(
        self,
        file_path: str,
        module_path: Path,
        var: dict[str, Any],
    ) -> dict:
        name = var.get("name", "")
        lineno = var.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("var", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "var",
            "docstring": var.get("doc"),
            "lineno": lineno,
            "symbol_metadata": var,
        }

    @staticmethod
    def _build_package_qualified_name(file_path: str, package_name: str) -> str:
        return f"{file_path}::package::{package_name}"

    @staticmethod
    def _build_qualified_name(
        module_path: Path,
        parts: t.Sequence[str],
        lineno: int | None = None,
    ) -> str:
        path_part = str(module_path)
        suffix = "::".join(parts)
        qualifier = f"{path_part}::{suffix}"
        if lineno:
            qualifier = f"{qualifier}@{lineno}"
        return qualifier

