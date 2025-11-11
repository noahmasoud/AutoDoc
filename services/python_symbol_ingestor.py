"""Service for persisting extracted Python symbol metadata."""

from __future__ import annotations

from pathlib import Path
import typing as t
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as SQLASession
else:
    SQLASession = Any

from db.models import PythonSymbol
from src.analyzer.extractor import ClassInfo, FunctionInfo, ModuleInfo, SymbolExtractor
from src.analyzer.parser import PythonParser


class PythonSymbolIngestor:
    """Extract Python symbols and persist them with docstrings."""

    def __init__(
        self,
        parser: PythonParser | None = None,
        extractor: SymbolExtractor | None = None,
    ) -> None:
        self._parser = parser or PythonParser()
        self._extractor = extractor or SymbolExtractor()

    def ingest_files(
        self,
        run_id: int,
        python_files: t.Sequence[str],
        db: SQLASession,
    ) -> list[PythonSymbol]:
        """Parse, extract, and persist symbols for the provided files."""
        persisted: list[PythonSymbol] = []
        for file_path in python_files:
            persisted.extend(self._ingest_single_file(run_id, file_path, db))
        return persisted

    def _ingest_single_file(
        self,
        run_id: int,
        file_path: str,
        db: SQLASession,
    ) -> list[PythonSymbol]:
        parse_result = self._parser.parse(file_path)
        if not parse_result.success or parse_result.ast_tree is None:
            return []

        module_info = self._extractor.extract(
            parse_result.ast_tree, parse_result.file_path
        )
        self._delete_existing_symbols(run_id, module_info.file_path, db)

        symbol_entries = list(self._flatten_module(module_info))

        persisted: list[PythonSymbol] = []
        for entry in symbol_entries:
            symbol = PythonSymbol(
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
            db.query(PythonSymbol)
            .filter(
                PythonSymbol.run_id == run_id,
                PythonSymbol.file_path == file_path,
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

    def _flatten_module(self, module: ModuleInfo) -> t.Iterable[dict]:
        module_path = self._normalize_path(module.file_path)

        yield {
            "file_path": module.file_path,
            "symbol_name": module_path.name or module_path.stem,
            "qualified_name": self._build_module_qualified_name(module.file_path),
            "symbol_type": "module",
            "docstring": module.module_docstring,
            "lineno": 1,
            "symbol_metadata": {"module_docstring": module.module_docstring},
        }

        for func in module.functions:
            yield self._build_function_entry(module.file_path, module_path, func)

        for cls in module.classes:
            yield self._build_class_entry(module.file_path, module_path, cls)
            for method in cls.methods:
                yield self._build_method_entry(
                    module.file_path, module_path, cls, method
                )

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
        func: FunctionInfo,
    ) -> dict:
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("function", func.name),
            lineno=func.lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": func.name,
            "qualified_name": qualified_name,
            "symbol_type": "function",
            "docstring": func.docstring,
            "lineno": func.lineno,
            "symbol_metadata": func.to_dict(),
        }

    def _build_class_entry(
        self,
        file_path: str,
        module_path: Path,
        cls: ClassInfo,
    ) -> dict:
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("class", cls.name),
            lineno=cls.lineno,
        )
        return {
            "file_path": file_path,
            "symbol_name": cls.name,
            "qualified_name": qualified_name,
            "symbol_type": "class",
            "docstring": cls.docstring,
            "lineno": cls.lineno,
            "symbol_metadata": cls.to_dict(),
        }

    def _build_method_entry(
        self,
        file_path: str,
        module_path: Path,
        cls: ClassInfo,
        method: FunctionInfo,
    ) -> dict:
        qualified_name = self._build_qualified_name(
            module_path,
            parts=("class", cls.name, "method", method.name),
            lineno=method.lineno,
        )
        metadata = method.to_dict()
        metadata["enclosing_class"] = cls.name
        return {
            "file_path": file_path,
            "symbol_name": method.name,
            "qualified_name": qualified_name,
            "symbol_type": "method",
            "docstring": method.docstring,
            "lineno": method.lineno,
            "symbol_metadata": metadata,
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
