"""Loading and schema validation for BeaconGrid records.

The loader is the single choke point where untrusted JSON enters the system.
It performs three jobs:

1. Parse JSON safely from a path or an in-memory string.
2. Assert the ``schema`` discriminator matches an accepted major version.
3. Delegate structural mapping to the typed model classes.

No third-party validators are used; the model classes raise ``SchemaError``
for missing required fields and the loader wraps everything in ``LoadError``
so callers have a single exception type to catch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .model import Policy, SchemaError, Session

_SESSION_SCHEMA = "beacongrid/session@"
_POLICY_SCHEMA = "beacongrid/policy@"
_ACCEPTED_MAJOR = "1"


class LoadError(Exception):
    """Raised for any failure while reading or validating a record."""


def _read_json(source: Union[str, Path]) -> Dict[str, Any]:
    text: str
    path = Path(source) if not isinstance(source, Path) else source
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
        else:
            # Treat the argument as a raw JSON string.
            text = str(source)
    except OSError as exc:  # pragma: no cover - defensive
        raise LoadError(f"could not read source: {exc}") from exc
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LoadError(f"invalid JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise LoadError("top-level JSON value must be an object")
    return record


def _check_schema(record: Dict[str, Any], prefix: str, kind: str) -> None:
    schema = record.get("schema")
    if not isinstance(schema, str) or not schema.startswith(prefix):
        raise LoadError(
            f"{kind}: expected schema starting with '{prefix}', got {schema!r}"
        )
    major = schema[len(prefix):].split(".", 1)[0]
    if major != _ACCEPTED_MAJOR:
        raise LoadError(
            f"{kind}: unsupported schema major version {major!r} "
            f"(this build accepts {_ACCEPTED_MAJOR})"
        )


def load_session(source: Union[str, Path]) -> Session:
    """Load and validate a session from a file path or JSON string."""

    record = _read_json(source)
    _check_schema(record, _SESSION_SCHEMA, "session")
    try:
        return Session.from_dict(record)
    except SchemaError as exc:
        raise LoadError(str(exc)) from exc


def load_policy(source: Union[str, Path]) -> Policy:
    """Load and validate a standalone policy from a path or JSON string."""

    record = _read_json(source)
    _check_schema(record, _POLICY_SCHEMA, "policy")
    try:
        return Policy.from_dict(record)
    except SchemaError as exc:
        raise LoadError(str(exc)) from exc
