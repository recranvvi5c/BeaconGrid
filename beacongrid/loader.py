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
