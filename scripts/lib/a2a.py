"""A2A Handoff Envelope — standardised Agent-to-Agent data exchange.

Provides the A2AEnvelope class for creating, validating, and serialising
structured handoff envelopes between agents in the agent-meta framework.

Usage:
    from scripts.lib.a2a import A2AEnvelope

    envelope = A2AEnvelope.create(
        source="orchestrator",
        target="developer",
        payload={"task": "Fix bug #248"},
        schema_ref="schemas/a2a-handoff.schema.json"
    )
    envelope.validate()
    json_str = envelope.to_json()
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

# -- handoff_id generation (thread-safe) ---------------------------------------

_ID_LOCK: threading.Lock = threading.Lock()
_ID_COUNTER: int = 0
_ID_DATE: str = ""


def generate_handoff_id() -> str:
    """Generate a unique handoff identifier.

    Format: HOFF-YYYYMMDD-NNN where NNN is a sequential counter per day,
    starting at 001 and incrementing with each call.  Thread-safe.
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    with _ID_LOCK:
        global _ID_COUNTER, _ID_DATE
        if _ID_DATE != today:
            _ID_COUNTER = 0
            _ID_DATE = today
        _ID_COUNTER += 1
        seq = _ID_COUNTER
    return f"HOFF-{today}-{seq:03d}"


# -- A2AEnvelope ---------------------------------------------------------------

HANDOFF_ID_RE = re.compile(r"^HOFF-\d{8}-\d{3,6}$")
PROTOCOL_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

VALID_NEGOTIATED_FORMATS: frozenset[str] = frozenset(
    {"json", "yaml", "text", "auto"}
)

REQUIRED_FIELDS: tuple[str, ...] = (
    "protocol_version",
    "handoff_id",
    "source_agent",
    "target_agent",
    "payload",
)


class A2AEnvelope:
    """Standardised Agent-to-Agent handoff envelope.

    Wraps a domain-specific payload with metadata for validation,
    supersession tracking, and traceability.

    Usage:
        envelope = A2AEnvelope.create(
            source="orchestrator",
            target="developer",
            payload={"task": "Implement login"},
        )
        envelope.validate()
        json_str = envelope.to_json()
    """

    PROTOCOL_VERSION: ClassVar[str] = "1.0.0"

    # Slots for memory efficiency and to prevent accidental attribute creation.
    __slots__ = (
        "protocol_version",
        "handoff_id",
        "source_agent",
        "target_agent",
        "payload",
        "schema_ref",
        "trace_parent",
        "trace_context",
        "retry_count",
        "max_retries",
        "batch",
        "requires_human_approval",
        "negotiated_format",
        "supersession",
        "metadata",
    )

    def __init__(
        self,
        source_agent: str,
        target_agent: str,
        payload: dict[str, Any] | list[dict[str, Any]],
        handoff_id: str | None = None,
        protocol_version: str = PROTOCOL_VERSION,
        schema_ref: str | None = None,
        trace_parent: str | None = None,
        trace_context: dict[str, Any] | None = None,
        retry_count: int = 0,
        max_retries: int = 3,
        batch: bool = False,
        requires_human_approval: bool = False,
        negotiated_format: str = "auto",
        supersession: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.protocol_version = protocol_version
        self.handoff_id = handoff_id if handoff_id is not None else generate_handoff_id()
        self.source_agent = source_agent
        self.target_agent = target_agent
        self.payload = payload
        self.schema_ref = schema_ref
        self.trace_parent = trace_parent
        self.trace_context = trace_context
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.batch = batch
        self.requires_human_approval = requires_human_approval
        self.negotiated_format = negotiated_format
        self.supersession = supersession
        self.metadata = metadata

    # -- factory ----------------------------------------------------------------

    @classmethod
    def create(
        cls,
        source: str,
        target: str,
        payload: dict[str, Any] | list[dict[str, Any]],
        schema_ref: str | None = None,
        trace_parent: str | None = None,
        trace_context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> A2AEnvelope:
        """Factory: create, validate, and return a new A2AEnvelope.

        Args:
            source: Role name of the producing agent.
            target: Role name of the consuming agent.
            payload: Domain-specific data to hand over.
            schema_ref: URI to the JSON Schema for the payload.
            trace_parent: handoff_id of the parent handoff.
            trace_context: Extended distributed tracing context.
            **kwargs: Additional envelope fields (batch, retry_count, etc.).

        Returns:
            A validated A2AEnvelope instance.

        Raises:
            ValueError: If validation fails.
        """
        envelope = cls(
            source_agent=source,
            target_agent=target,
            payload=payload,
            schema_ref=schema_ref,
            trace_parent=trace_parent,
            trace_context=trace_context,
            **kwargs,
        )
        envelope.validate()
        return envelope

    # -- validation -------------------------------------------------------------

    @staticmethod
    def _format_errors(errors: list[str]) -> str:
        return "A2AEnvelope validation failed:\n  - " + "\n  - ".join(errors)

    def validate(self) -> bool:
        """Validate the envelope against the A2A schema.

        Uses ``jsonschema`` if installed; otherwise falls back to manual
        validation of required fields and format constraints.

        Returns:
            True if valid.

        Raises:
            ValueError: With details of all validation failures.
        """
        errors: list[str] = []

        # Try jsonschema first.
        try:
            import jsonschema  # type: ignore[import-untyped]
        except ImportError:
            pass
        else:
            self._validate_with_jsonschema(errors, jsonschema)
            if errors:
                raise ValueError(self._format_errors(errors))
            return True

        # Fallback: manual validation.
        self._validate_required_fields(errors)
        self._validate_formats(errors)
        self._validate_enums(errors)
        self._validate_supersession(errors)

        if errors:
            raise ValueError(self._format_errors(errors))
        return True

    def _validate_with_jsonschema(
        self, errors: list[str], jsonschema: Any
    ) -> None:
        """Validate using the jsonschema library."""
        schema_path = (
            Path(__file__).parent.parent.parent
            / "schemas"
            / "a2a-handoff.schema.json"
        )
        try:
            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f"Schema load error: {exc}")
            return

        try:
            jsonschema.validate(instance=self.to_dict(), schema=schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"jsonschema: {exc.message}")
        except jsonschema.SchemaError as exc:
            errors.append(f"jsonschema schema error: {exc}")

    def _validate_required_fields(self, errors: list[str]) -> None:
        """Check all required fields are present and non-empty."""
        for field in REQUIRED_FIELDS:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Required field '{field}' is missing or empty")
        if self.retry_count < 0:
            errors.append(f"retry_count must be >= 0, got {self.retry_count}")
        if self.max_retries < 1:
            errors.append(f"max_retries must be >= 1, got {self.max_retries}")

    def _validate_formats(self, errors: list[str]) -> None:
        """Validate format patterns for handoff_id, protocol_version, etc."""
        if self.handoff_id and not HANDOFF_ID_RE.match(self.handoff_id):
            errors.append(
                f"handoff_id '{self.handoff_id}' does not match "
                f"pattern HOFF-YYYYMMDD-NNN"
            )
        if self.protocol_version and not PROTOCOL_VERSION_RE.match(
            self.protocol_version
        ):
            errors.append(
                f"protocol_version '{self.protocol_version}' is not valid SemVer"
            )
        if self.trace_parent and not HANDOFF_ID_RE.match(self.trace_parent):
            errors.append(
                f"trace_parent '{self.trace_parent}' does not match "
                f"pattern HOFF-YYYYMMDD-NNN"
            )
        if isinstance(self.payload, list) and not self.batch:
            # Payload can be array only when batch mode is active.
            pass  # schema allows array payload; we don't strictly enforce batch

    def _validate_enums(self, errors: list[str]) -> None:
        """Validate enum-constrained fields."""
        fmt = self.negotiated_format
        if fmt is None:
            errors.append("negotiated_format must not be None")
        elif fmt not in VALID_NEGOTIATED_FORMATS:
            errors.append(
                f"negotiated_format '{fmt}' is not one of "
                f"{sorted(VALID_NEGOTIATED_FORMATS)}"
            )

    def _validate_supersession(self, errors: list[str]) -> None:
        """Validate supersession sub-object if present."""
        ss = self.supersession
        if ss is None:
            return
        if "supersedes" not in ss:
            return  # supersedes is the trigger field; not required otherwise
        if "reason" not in ss:
            errors.append("supersession.reason is required when supersedes is set")
        if "timestamp" not in ss:
            errors.append(
                "supersession.timestamp is required when supersedes is set"
            )
        if not HANDOFF_ID_RE.match(ss.get("supersedes", "")):
            errors.append(
                f"supersession.supersedes '{ss.get('supersedes')}' "
                f"does not match pattern HOFF-YYYYMMDD-NNN"
            )

    # -- serialisation ----------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return the envelope as a dictionary (only non-None fields)."""
        result: dict[str, Any] = {
            "protocol_version": self.protocol_version,
            "handoff_id": self.handoff_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "payload": self.payload,
        }
        if self.schema_ref is not None:
            result["schema_ref"] = self.schema_ref
        if self.trace_parent is not None:
            result["trace_parent"] = self.trace_parent
        if self.trace_context is not None:
            result["trace_context"] = self.trace_context
        if self.retry_count != 0:
            result["retry_count"] = self.retry_count
        if self.max_retries != 3:
            result["max_retries"] = self.max_retries
        if self.batch:
            result["batch"] = self.batch
        if self.requires_human_approval:
            result["requires_human_approval"] = self.requires_human_approval
        if self.negotiated_format != "auto":
            result["negotiated_format"] = self.negotiated_format
        if self.supersession is not None:
            result["supersession"] = self.supersession
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result

    def to_json(self, indent: int = 2) -> str:
        """Return the envelope as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> A2AEnvelope:
        """Create an envelope from a JSON string.

        Parses the JSON, validates the resulting envelope, and returns it.

        Args:
            json_str: A JSON string representing an A2A envelope.

        Returns:
            A validated A2AEnvelope instance.

        Raises:
            ValueError: If the JSON is invalid or validation fails.
            KeyError: If required fields are missing.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object, got {type(data).__name__}"
            )

        envelope = cls(
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            payload=data["payload"],
            handoff_id=data["handoff_id"],
            protocol_version=data["protocol_version"],
            schema_ref=data.get("schema_ref"),
            trace_parent=data.get("trace_parent"),
            trace_context=data.get("trace_context"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            batch=data.get("batch", False),
            requires_human_approval=data.get("requires_human_approval", False),
            negotiated_format=data.get("negotiated_format", "auto"),
            supersession=data.get("supersession"),
            metadata=data.get("metadata"),
        )
        envelope.validate()
        return envelope

    # -- equality & representation ---------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, A2AEnvelope):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        return (
            f"A2AEnvelope(handoff_id={self.handoff_id!r}, "
            f"source_agent={self.source_agent!r}, "
            f"target_agent={self.target_agent!r})"
        )

