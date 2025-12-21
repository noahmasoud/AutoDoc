"""Service for persisting extracted JavaScript symbol metadata."""

from __future__ import annotations

from pathlib import Path
import typing as t
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as SQLASession
else:
    SQLASession = Any

from db.models import JavaScriptSymbol
from services.javascript_parser import JavaScriptParser


class JavaScriptSymbolIngestor:
    """Extract JavaScript symbols and persist them with JSDoc comments."""

    def __init__(
        self,
        parser: JavaScriptParser | None = None,
    ) -> None:
        self._parser = parser or JavaScriptParser()

    def ingest_files(
        self,
        run_id: int,
        js_files: t.Sequence[str],
        db: SQLASession,
    ) -> list[JavaScriptSymbol]:
        """Parse, extract, and persist symbols for the provided files."""
        persisted: list[JavaScriptSymbol] = []
        for file_path in js_files:
            persisted.extend(self._ingest_single_file(run_id, file_path, db))
        return persisted

    def _ingest_single_file(
        self,
        run_id: int,
        file_path: str,
        db: SQLASession,
    ) -> list[JavaScriptSymbol]:
        try:
            ast = self._parser.parse_file(file_path)
            symbols_dict = self._parser.extract_public_symbols(ast)
        except Exception:
            # If parsing fails, return empty list
            return []

        self._delete_existing_symbols(run_id, file_path, db)

        symbol_entries = list(self._flatten_symbols(file_path, symbols_dict, ast))

        persisted: list[JavaScriptSymbol] = []
        for entry in symbol_entries:
            symbol = JavaScriptSymbol(
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
            db.query(JavaScriptSymbol)
            .filter(
                JavaScriptSymbol.run_id == run_id,
                JavaScriptSymbol.file_path == file_path,
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

        # Module-level entry
        yield {
            "file_path": file_path,
            "symbol_name": module_path.name or module_path.stem,
            "qualified_name": self._build_module_qualified_name(file_path),
            "symbol_type": "module",
            "docstring": None,  # Could extract from leading comments
            "lineno": 1,
            "symbol_metadata": {},
        }

        # Process classes
        for cls in symbols_dict.get("classes", []):
            yield self._build_class_entry(file_path, module_path, cls)

        # Process functions
        for func in symbols_dict.get("functions", []):
            yield self._build_function_entry(file_path, module_path, func)

        # Process interfaces
        for interface in symbols_dict.get("interfaces", []):
            yield self._build_interface_entry(file_path, module_path, interface)

        # Process types
        for type_alias in symbols_dict.get("types", []):
            yield self._build_type_entry(file_path, module_path, type_alias)

        # Process enums
        for enum in symbols_dict.get("enums", []):
            yield self._build_enum_entry(file_path, module_path, enum)

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
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("function", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "function",
            "docstring": None,  # Could extract JSDoc from AST
            "lineno": lineno,
            "symbol_metadata": func,
        }

    def _build_class_entry(
        self,
        file_path: str,
        module_path: Path,
        cls: dict[str, Any],
    ) -> dict:
        name = cls.get("name", "")
        lineno = cls.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("class", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "class",
            "docstring": None,  # Could extract JSDoc from AST
            "lineno": lineno,
            "symbol_metadata": cls,
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
            "docstring": None,
            "lineno": lineno,
            "symbol_metadata": interface,
        }

    def _build_type_entry(
        self,
        file_path: str,
        module_path: Path,
        type_alias: dict[str, Any],
    ) -> dict:
        name = type_alias.get("name", "")
        lineno = type_alias.get("line")
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
            "docstring": None,
            "lineno": lineno,
            "symbol_metadata": type_alias,
        }

    def _build_enum_entry(
        self,
        file_path: str,
        module_path: Path,
        enum: dict[str, Any],
    ) -> dict:
        name = enum.get("name", "")
        lineno = enum.get("line")
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("enum", name),
            lineno=lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": name,
            "qualified_name": qualified_name,
            "symbol_type": "enum",
            "docstring": None,
            "lineno": lineno,
            "symbol_metadata": enum,
        }

    @staticmethod
    def _build_module_qualified_name(file_path: str) -> str:
        return f"{file_path}::module"

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

