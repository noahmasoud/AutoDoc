"""
SQLAlchemy models for AutoDoc database schema.

Per SRS 7.1 Data Requirements and retention policy 7.2.
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Text,
    ForeignKey,
    Integer,
    DateTime,
    JSON,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base


class Run(Base):
    """
    Run entity: tracks CI/CD analysis runs.

    Per SRS 7.1: Run history and status tracking.
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    commit_sha: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )  # Index per requirements
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Awaiting Review",
    )
    correlation_id: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships with cascade delete
    changes: Mapped[list["Change"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    patches: Mapped[list["Patch"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
    python_symbols: Mapped[list["PythonSymbol"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('Awaiting Review', 'Success', 'Failed', 'Manual Action Required', 'Completed (no patches)')",
            name="check_run_status",
        ),
    )


class Change(Base):
    """
    Change entity: stores analyzer findings.

    Per SRS 7.1: Stores analyzer findings for code changes.
    """

    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index per requirements
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)
    signature_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    signature_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationship
    run: Mapped["Run"] = relationship(back_populates="changes")

    __table_args__ = (
        CheckConstraint(
            "change_type IN ('added', 'removed', 'modified')",
            name="check_change_type",
        ),
    )


class PythonSymbol(Base):
    """
    PythonSymbol entity: stores extracted Python symbol metadata and docstrings.

    Supports documentation pipelines that require persisted symbol data.
    """

    __tablename__ = "python_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    symbol_name: Mapped[str] = mapped_column(Text, nullable=False)
    qualified_name: Mapped[str] = mapped_column(Text, nullable=False)
    symbol_type: Mapped[str] = mapped_column(Text, nullable=False)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)
    lineno: Mapped[int | None] = mapped_column(Integer, nullable=True)
    symbol_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="python_symbols")

    __table_args__ = (
        CheckConstraint(
            "symbol_type IN ('module', 'class', 'function', 'method')",
            name="check_python_symbol_type",
        ),
        UniqueConstraint(
            "run_id",
            "qualified_name",
            name="uq_python_symbols_run_path_name",
        ),
    )


class Rule(Base):
    """
    Rule entity: configuration rules for documentation patterns.

    Per SRS 7.1: CRUD required by UI.
    """

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        index=True,
    )  # UNIQUE and indexed
    selector: Mapped[str] = mapped_column(Text, nullable=False)
    space_key: Mapped[str] = mapped_column(Text, nullable=False)
    page_id: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    auto_approve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationship
    template: Mapped["Template | None"] = relationship(back_populates="rules")


class Template(Base):
    """
    Template entity: documentation templates.

    Per SRS 7.1: Template-driven patch generation.
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        index=True,
    )  # UNIQUE and indexed
    format: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationship
    rules: Mapped[list["Rule"]] = relationship(back_populates="template")

    __table_args__ = (
        CheckConstraint(
            "format IN ('Markdown', 'Storage')",
            name="check_template_format",
        ),
    )


class Patch(Base):
    """
    Patch entity: tracks documentation updates and audit trail.

    Per SRS 7.1: Tracks audit per patch.
    """

    __tablename__ = "patches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index per requirements
    )
    page_id: Mapped[str] = mapped_column(Text, nullable=False)
    diff_before: Mapped[str] = mapped_column(Text, nullable=False)
    diff_after: Mapped[str] = mapped_column(Text, nullable=False)
    diff_unified: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Proposed",
    )

    # Relationship
    run: Mapped["Run"] = relationship(back_populates="patches")

    __table_args__ = (
        CheckConstraint(
            "status IN ('Proposed', 'Approved', 'Rejected', 'Applied', 'RolledBack')",
            name="check_patch_status",
        ),
    )


class Connection(Base):
    """
    Connection entity: stores Confluence connection configuration.

    Per FR-28 and NFR-9: Token is encrypted at rest and never logged.
    Only one connection is allowed per system.
    """

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    confluence_base_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    space_key: Mapped[str] = mapped_column(Text, nullable=False)
    # Encrypted token - never store plaintext (NFR-9)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    # Metadata
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
