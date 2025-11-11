"""Pydantic schemas for persisted Python symbols."""

from __future__ import annotations

from pydantic import BaseModel


class PythonSymbolOut(BaseModel):
    """Serialized Python symbol with docstring metadata."""

    file_path: str
    symbol_name: str
    qualified_name: str
    symbol_type: str
    docstring: str | None = None
    lineno: int | None = None
    symbol_metadata: dict | None = None

    model_config = {"from_attributes": True}


class PythonSymbolList(BaseModel):
    """List wrapper for Python symbols."""

    items: list[PythonSymbolOut]


