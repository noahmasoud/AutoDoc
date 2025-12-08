"""Change Detector for Python Symbols - SCRUM-28"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from .extractor import ModuleInfo, FunctionInfo, ClassInfo


class ChangeType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class SymbolType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"


@dataclass
class SymbolChange:
    change_type: ChangeType
    symbol_type: SymbolType
    symbol_name: str
    is_breaking: bool = False
    breaking_reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "symbol_type": self.symbol_type.value,
            "symbol_name": self.symbol_name,
            "is_breaking": self.is_breaking,
            "breaking_reasons": self.breaking_reasons,
            "details": self.details,
        }


@dataclass
class ChangeReport:
    file_path: str
    old_version: str = "old"
    new_version: str = "new"
    added: list[SymbolChange] = field(default_factory=list)
    removed: list[SymbolChange] = field(default_factory=list)
    modified: list[SymbolChange] = field(default_factory=list)
    has_breaking_changes: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "added": [c.to_dict() for c in self.added],
            "removed": [c.to_dict() for c in self.removed],
            "modified": [c.to_dict() for c in self.modified],
            "has_breaking_changes": self.has_breaking_changes,
            "summary": {
                "total_changes": len(self.added)
                + len(self.removed)
                + len(self.modified),
                "added_count": len(self.added),
                "removed_count": len(self.removed),
                "modified_count": len(self.modified),
                "breaking_count": sum(
                    1
                    for c in self.added + self.removed + self.modified
                    if c.is_breaking
                ),
            },
        }


class FunctionChangeDetector:
    def compare(
        self, old_func: Optional[FunctionInfo], new_func: Optional[FunctionInfo]
    ) -> Optional[SymbolChange]:
        if old_func is None and new_func is not None:
            return SymbolChange(
                change_type=ChangeType.ADDED,
                symbol_type=SymbolType.METHOD
                if new_func.is_method
                else SymbolType.FUNCTION,
                symbol_name=new_func.name,
            )
        if old_func is not None and new_func is None:
            return SymbolChange(
                change_type=ChangeType.REMOVED,
                symbol_type=SymbolType.METHOD
                if old_func.is_method
                else SymbolType.FUNCTION,
                symbol_name=old_func.name,
                is_breaking=old_func.is_public,
                breaking_reasons=["Public function removed"]
                if old_func.is_public
                else [],
            )
        if old_func and new_func:
            return self._detect_modifications(old_func, new_func)
        return None

    def _detect_modifications(
        self, old_func: FunctionInfo, new_func: FunctionInfo
    ) -> Optional[SymbolChange]:
        breaking_reasons = []
        details = {}
        old_params = {p.name: p for p in old_func.parameters}
        new_params = {p.name: p for p in new_func.parameters}
        breaking_reasons.extend(
            f"Parameter '{name}' removed"
            for name in old_params
            if name not in new_params
        )
        for name, new_param in new_params.items():
            if name not in old_params:
                if new_param.default is None:
                    breaking_reasons.append(f"Required parameter '{name}' added")
                else:
                    details["optional_parameter_added"] = name
        for name, old_param in old_params.items():
            if name in new_params:
                old_type = old_param.annotation
                new_type = new_params[name].annotation
                if old_type and new_type and old_type != new_type:
                    breaking_reasons.append(
                        f"Parameter '{name}' type changed: {old_type} -> {new_type}"
                    )
        if (
            old_func.return_type
            and new_func.return_type
            and old_func.return_type != new_func.return_type
        ):
            breaking_reasons.append(
                f"Return type changed: {old_func.return_type} -> {new_func.return_type}"
            )
        if old_func.is_async != new_func.is_async:
            breaking_reasons.append(
                f"Changed from {'async' if old_func.is_async else 'sync'} to {'async' if new_func.is_async else 'sync'}"
            )
        if len(old_params) != len(new_params):
            details["parameter_count_changed"] = True
        if old_func.docstring != new_func.docstring:
            details["docstring_changed"] = True
        if old_func.decorators != new_func.decorators:
            details["decorators_changed"] = True
        if not breaking_reasons and not details:
            return None
        return SymbolChange(
            change_type=ChangeType.MODIFIED,
            symbol_type=SymbolType.METHOD
            if new_func.is_method
            else SymbolType.FUNCTION,
            symbol_name=new_func.name,
            is_breaking=len(breaking_reasons) > 0 and new_func.is_public,
            breaking_reasons=breaking_reasons if new_func.is_public else [],
            details=details,
        )


class ClassChangeDetector:
    def __init__(self):
        self.func_detector = FunctionChangeDetector()

    def compare(
        self, old_class: Optional[ClassInfo], new_class: Optional[ClassInfo]
    ) -> Optional[SymbolChange]:
        if old_class is None and new_class is not None:
            return SymbolChange(
                change_type=ChangeType.ADDED,
                symbol_type=SymbolType.CLASS,
                symbol_name=new_class.name,
            )
        if old_class is not None and new_class is None:
            return SymbolChange(
                change_type=ChangeType.REMOVED,
                symbol_type=SymbolType.CLASS,
                symbol_name=old_class.name,
                is_breaking=old_class.is_public,
                breaking_reasons=["Public class removed"]
                if old_class.is_public
                else [],
            )
        if old_class and new_class:
            return self._detect_modifications(old_class, new_class)
        return None

    def _detect_modifications(
        self, old_class: ClassInfo, new_class: ClassInfo
    ) -> Optional[SymbolChange]:
        breaking_reasons = []
        details = {}
        if set(old_class.base_classes) != set(new_class.base_classes):
            breaking_reasons.append("Base classes changed")
            details["base_classes"] = {
                "old": old_class.base_classes,
                "new": new_class.base_classes,
            }
        old_methods = {m.name: m for m in old_class.methods}
        new_methods = {m.name: m for m in new_class.methods}
        method_changes = []
        for name, method in old_methods.items():
            if name not in new_methods and method.is_public:
                breaking_reasons.append(f"Public method '{name}' removed")
                method_changes.append(("removed", name))
        for name, old_method in old_methods.items():
            if name in new_methods:
                change = self.func_detector.compare(old_method, new_methods[name])
                if change and change.is_breaking:
                    breaking_reasons.extend(
                        [f"Method '{name}': {r}" for r in change.breaking_reasons]
                    )
                    method_changes.append(("modified", name))
        if method_changes:
            details["method_changes"] = method_changes
        if old_class.docstring != new_class.docstring:
            details["docstring_changed"] = True
        if not breaking_reasons and not details:
            return None
        return SymbolChange(
            change_type=ChangeType.MODIFIED,
            symbol_type=SymbolType.CLASS,
            symbol_name=new_class.name,
            is_breaking=len(breaking_reasons) > 0 and new_class.is_public,
            breaking_reasons=breaking_reasons if new_class.is_public else [],
            details=details,
        )


class ChangeDetector:
    def __init__(self):
        self.func_detector = FunctionChangeDetector()
        self.class_detector = ClassChangeDetector()

    def detect_changes(
        self,
        old_module: ModuleInfo,
        new_module: ModuleInfo,
        old_version: str = "old",
        new_version: str = "new",
    ) -> ChangeReport:
        report = ChangeReport(
            file_path=new_module.file_path,
            old_version=old_version,
            new_version=new_version,
        )
        self._compare_symbols(
            old_module.functions, new_module.functions, self.func_detector, report
        )
        self._compare_symbols(
            old_module.classes, new_module.classes, self.class_detector, report
        )
        all_changes = report.added + report.removed + report.modified
        report.has_breaking_changes = any(c.is_breaking for c in all_changes)
        return report

    def _compare_symbols(self, old_symbols, new_symbols, detector, report):
        old_map = {s.name: s for s in old_symbols}
        new_map = {s.name: s for s in new_symbols}
        for name, symbol in new_map.items():
            if name not in old_map:
                change = detector.compare(None, symbol)
                if change:
                    report.added.append(change)
        for name, symbol in old_map.items():
            if name not in new_map:
                change = detector.compare(symbol, None)
                if change:
                    report.removed.append(change)
        for name, old_symbol in old_map.items():
            if name in new_map:
                change = detector.compare(old_symbol, new_map[name])
                if change:
                    report.modified.append(change)


def detect_changes(
    old_module: ModuleInfo,
    new_module: ModuleInfo,
    old_version: str = "old",
    new_version: str = "new",
) -> ChangeReport:
    detector = ChangeDetector()
    return detector.detect_changes(old_module, new_module, old_version, new_version)
