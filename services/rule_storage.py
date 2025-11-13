"""Storage helpers for rule definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.models import Rule

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from schemas.rules import RuleCreate, RuleUpdate


class RuleStorageError(Exception):
    """Base exception for rule storage issues."""


class RuleNotFoundError(RuleStorageError):
    """Raised when a rule is not found."""


class RuleConflictError(RuleStorageError):
    """Raised when a rule violates a uniqueness constraint."""


def list_rules(session: Session) -> list[Rule]:
    """Return all rules ordered by ID."""
    return session.execute(select(Rule).order_by(Rule.id)).scalars().all()


def get_rule(session: Session, rule_id: int) -> Rule:
    """Fetch a single rule or raise if it does not exist."""
    rule = session.get(Rule, rule_id)
    if rule is None:
        raise RuleNotFoundError(f"Rule {rule_id} not found")
    return rule


def create_rule(session: Session, payload: RuleCreate) -> Rule:
    """Create a new rule record."""
    rule = Rule(**payload.model_dump())
    session.add(rule)
    try:
        session.flush()
    except IntegrityError as exc:  # pragma: no cover - exercised in API layer
        session.rollback()
        raise RuleConflictError("Rule name must be unique") from exc
    session.refresh(rule)
    return rule


def update_rule(
    session: Session,
    rule_id: int,
    payload: RuleUpdate,
) -> Rule:
    """Update an existing rule."""
    rule = get_rule(session, rule_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    try:
        session.flush()
    except IntegrityError as exc:  # pragma: no cover - exercised in API layer
        session.rollback()
        raise RuleConflictError("Rule name must be unique") from exc
    session.refresh(rule)
    return rule


def delete_rule(session: Session, rule_id: int) -> None:
    """Delete a rule by ID."""
    rule = get_rule(session, rule_id)
    session.delete(rule)
    session.flush()
