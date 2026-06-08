"""Tests for scripts.lib.a2a — A2AEnvelope and handoff_id generation."""

from __future__ import annotations

import json
import re
import threading

import pytest

from scripts.lib.a2a import (
    A2AEnvelope,
    HANDOFF_ID_RE,
    generate_handoff_id,
)


# -- generate_handoff_id -------------------------------------------------------


class TestHandoffId:
    """Tests for generate_handoff_id()."""

    def test_format(self) -> None:
        """handoff_id matches HOFF-YYYYMMDD-NNN."""
        hid = generate_handoff_id()
        assert HANDOFF_ID_RE.match(hid), f"Invalid format: {hid}"

    def test_increment(self) -> None:
        """Sequential calls produce incrementing suffix."""
        id1 = generate_handoff_id()
        id2 = generate_handoff_id()
        id3 = generate_handoff_id()

        suffix1 = int(id1.rsplit("-", 1)[1])
        suffix2 = int(id2.rsplit("-", 1)[1])
        suffix3 = int(id3.rsplit("-", 1)[1])

        assert suffix2 == suffix1 + 1
        assert suffix3 == suffix2 + 1

    def test_thread_safety(self) -> None:
        """Parallel ID generation produces unique IDs."""
        ids: list[str] = []
        lock = threading.Lock()
        errors: list[str] = []

        def worker() -> None:
            try:
                for _ in range(50):
                    hid = generate_handoff_id()
                    with lock:
                        ids.append(hid)
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Worker errors: {errors}"
        assert len(ids) == 500
        assert len(set(ids)) == 500, "Duplicate handoff_ids detected"
        for hid in ids:
            assert HANDOFF_ID_RE.match(hid), f"Bad id: {hid}"


# -- A2AEnvelope: construction & factory ---------------------------------------


class TestA2AEnvelopeCreate:
    """Tests for A2AEnvelope.create() and __init__."""

    def test_create_simple_envelope(self) -> None:
        """Minimal envelope with only required fields."""
        env = A2AEnvelope.create(
            source="orchestrator",
            target="developer",
            payload={"task": "Fix bug #42"},
        )
        assert env.protocol_version == "1.0.0"
        assert HANDOFF_ID_RE.match(env.handoff_id)
        assert env.source_agent == "orchestrator"
        assert env.target_agent == "developer"
        assert env.payload == {"task": "Fix bug #42"}
        # Defaults
        assert env.retry_count == 0
        assert env.max_retries == 3
        assert env.batch is False
        assert env.requires_human_approval is False
        assert env.negotiated_format == "auto"

    def test_create_with_all_fields(self) -> None:
        """Envelope with every optional field populated."""
        env = A2AEnvelope.create(
            source="se-architect",
            target="se-critic",
            payload={"feature_id": "REQ-001"},
            schema_ref="schemas/se-decomposition.schema.json",
            trace_parent="HOFF-20260601-001",
            trace_context={
                "trace_id": "trace-abc123",
                "span_id": "span-xyz789",
                "viz_task_id": "viz-001",
            },
            retry_count=1,
            max_retries=5,
            batch=True,
            requires_human_approval=True,
            negotiated_format="yaml",
            supersession={
                "supersedes": "HOFF-20260601-001",
                "reason": "Critic rejection",
                "timestamp": "2026-06-02T10:00:00Z",
                "history": [
                    "HOFF-20260530-042",
                    "HOFF-20260601-001",
                ],
            },
            metadata={"provider": "opencode", "priority": "high"},
        )
        assert env.schema_ref == "schemas/se-decomposition.schema.json"
        assert env.trace_parent == "HOFF-20260601-001"
        assert env.trace_context["trace_id"] == "trace-abc123"
        assert env.trace_context["viz_task_id"] == "viz-001"
        assert env.retry_count == 1
        assert env.max_retries == 5
        assert env.batch is True
        assert env.requires_human_approval is True
        assert env.negotiated_format == "yaml"
        assert env.supersession is not None
        assert env.supersession["reason"] == "Critic rejection"
        assert env.metadata is not None
        assert env.metadata["provider"] == "opencode"

    def test_create_with_list_payload(self) -> None:
        """Payload can be a list (batch mode payload)."""
        env = A2AEnvelope.create(
            source="orchestrator",
            target="developer",
            payload=[
                {"task_id": "1", "task": "Fix bug"},
                {"task_id": "2", "task": "Add feature"},
            ],
            batch=True,
        )
        assert isinstance(env.payload, list)
        assert len(env.payload) == 2


# -- A2AEnvelope: validation ---------------------------------------------------


class TestA2AEnvelopeValidation:
    """Tests for A2AEnvelope.validate()."""

    def test_validation_missing_source(self) -> None:
        """Missing source_agent raises ValueError."""
        with pytest.raises(ValueError, match="source_agent"):
            A2AEnvelope(
                source_agent="",
                target_agent="developer",
                payload={"x": 1},
            ).validate()

    def test_validation_missing_target(self) -> None:
        """Missing target_agent raises ValueError."""
        with pytest.raises(ValueError, match="target_agent"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="",
                payload={"x": 1},
            ).validate()

    def test_validation_missing_payload(self) -> None:
        """None payload raises ValueError."""
        with pytest.raises(ValueError, match="payload"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload=None,  # type: ignore[arg-type]
            ).validate()

    def test_validation_bad_handoff_id(self) -> None:
        """Invalid handoff_id format raises ValueError."""
        with pytest.raises(ValueError, match="handoff_id"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                handoff_id="garbage",
            ).validate()

    def test_validation_bad_protocol_version(self) -> None:
        """Invalid protocol_version raises ValueError."""
        with pytest.raises(ValueError, match="protocol_version"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                protocol_version="v1",
            ).validate()

    def test_validation_bad_trace_parent(self) -> None:
        """Invalid trace_parent format raises ValueError."""
        with pytest.raises(ValueError, match="trace_parent"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                trace_parent="not-an-id",
            ).validate()

    def test_validation_bad_negotiated_format(self) -> None:
        """Invalid negotiated_format raises ValueError."""
        with pytest.raises(ValueError, match="negotiated_format"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                negotiated_format="xml",
            ).validate()

    def test_validation_supersession_missing_reason(self) -> None:
        """supersession with supersedes but no reason raises ValueError."""
        with pytest.raises(ValueError, match="supersession.reason"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                supersession={
                    "supersedes": "HOFF-20260601-001",
                    "timestamp": "2026-06-02T10:00:00Z",
                },
            ).validate()

    def test_validation_negotiated_format_none(self) -> None:
        """None negotiated_format raises ValueError."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"x": 1},
            negotiated_format=None,  # type: ignore[arg-type]
        )
        with pytest.raises(ValueError, match="negotiated_format"):
            env.validate()

    def test_validation_retry_count_negative(self) -> None:
        """Negative retry_count raises ValueError."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"x": 1},
            retry_count=-1,
        )
        with pytest.raises(ValueError, match="retry_count"):
            env.validate()

    def test_validation_max_retries_zero(self) -> None:
        """max_retries of 0 raises ValueError."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"x": 1},
            max_retries=0,
        )
        with pytest.raises(ValueError, match="max_retries"):
            env.validate()

    def test_validation_supersession_bad_handoff_id(self) -> None:
        """supersession.supersedes with bad format raises ValueError."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"x": 1},
            supersession={
                "supersedes": "not-a-valid-hoff-id",
                "reason": "bad format",
                "timestamp": "2026-06-02T10:00:00Z",
            },
        )
        with pytest.raises(ValueError, match="supersession.supersedes"):
            env.validate()

    def test_validation_supersession_missing_timestamp(self) -> None:
        """supersession with supersedes but no timestamp raises ValueError."""
        with pytest.raises(ValueError, match="supersession.timestamp"):
            A2AEnvelope(
                source_agent="orchestrator",
                target_agent="developer",
                payload={"x": 1},
                supersession={
                    "supersedes": "HOFF-20260601-001",
                    "reason": "Fix needed",
                },
            ).validate()


# -- A2AEnvelope: serialisation ------------------------------------------------


class TestA2AEnvelopeSerialisation:
    """Tests for to_dict(), to_json(), from_json()."""

    def test_to_dict_only_non_none(self) -> None:
        """to_dict() omits default-valued optional fields."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"task": "test"},
        )
        d = env.to_dict()
        assert "protocol_version" in d
        assert "handoff_id" in d
        assert "source_agent" in d
        assert "target_agent" in d
        assert "payload" in d
        # Default-valued fields should be absent.
        assert "retry_count" not in d  # default 0
        assert "max_retries" not in d  # default 3
        assert "batch" not in d  # default False
        assert "requires_human_approval" not in d
        assert "negotiated_format" not in d  # default "auto"

    def test_to_dict_includes_non_default(self) -> None:
        """to_dict() includes fields that differ from default."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"task": "test"},
            retry_count=2,
            batch=True,
            negotiated_format="yaml",
        )
        d = env.to_dict()
        assert d["retry_count"] == 2
        assert d["batch"] is True
        assert d["negotiated_format"] == "yaml"

    def test_json_serialization_roundtrip(self) -> None:
        """to_json() → from_json() produces an equal envelope."""
        original = A2AEnvelope.create(
            source="orchestrator",
            target="developer",
            payload={"task": "Fix bug #42", "priority": "high"},
            schema_ref="schemas/a2a-handoff.schema.json",
            trace_parent="HOFF-20260601-001",
            trace_context={"trace_id": "t1", "span_id": "s1"},
        )
        json_str = original.to_json()
        # Verify valid JSON.
        parsed = json.loads(json_str)
        assert parsed["source_agent"] == "orchestrator"
        assert parsed["payload"]["task"] == "Fix bug #42"

        # Roundtrip.
        restored = A2AEnvelope.from_json(json_str)
        assert restored == original
        assert restored.handoff_id == original.handoff_id
        assert restored.trace_parent == original.trace_parent

    def test_from_json_invalid_json(self) -> None:
        """from_json() raises ValueError on malformed JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            A2AEnvelope.from_json("{not valid json")

    def test_from_json_not_a_dict(self) -> None:
        """from_json() raises ValueError when JSON is not an object."""
        with pytest.raises(ValueError, match="JSON object"):
            A2AEnvelope.from_json("[1, 2, 3]")

    def test_from_json_missing_required(self) -> None:
        """from_json() raises KeyError when required fields missing."""
        with pytest.raises(KeyError):
            A2AEnvelope.from_json('{"handoff_id": "HOFF-20260601-001"}')

    def test_from_json_missing_handoff_id(self) -> None:
        """from_json() raises KeyError when handoff_id is missing."""
        with pytest.raises(KeyError):
            A2AEnvelope.from_json(
                '{"source_agent": "a", "target_agent": "b", '
                '"payload": {"x": 1}, "protocol_version": "1.0.0"}'
            )

    def test_from_json_missing_protocol_version(self) -> None:
        """from_json() raises KeyError when protocol_version is missing."""
        with pytest.raises(KeyError):
            A2AEnvelope.from_json(
                '{"source_agent": "a", "target_agent": "b", '
                '"payload": {"x": 1}, "handoff_id": "HOFF-20260601-001"}'
            )


# -- A2AEnvelope: equality & representation ------------------------------------


class TestA2AEnvelopeEqRepr:
    """Tests for __eq__ and __repr__."""

    def test_equality_equal(self) -> None:
        """Two envelopes with identical fields are equal."""
        e1 = A2AEnvelope(
            source_agent="orch",
            target_agent="dev",
            payload={"t": 1},
            handoff_id="HOFF-20260601-001",
        )
        e2 = A2AEnvelope(
            source_agent="orch",
            target_agent="dev",
            payload={"t": 1},
            handoff_id="HOFF-20260601-001",
        )
        assert e1 == e2

    def test_equality_different(self) -> None:
        """Two envelopes with different payload are not equal."""
        e1 = A2AEnvelope(
            source_agent="orch",
            target_agent="dev",
            payload={"t": 1},
            handoff_id="HOFF-20260601-001",
        )
        e2 = A2AEnvelope(
            source_agent="orch",
            target_agent="dev",
            payload={"t": 2},
            handoff_id="HOFF-20260601-001",
        )
        assert e1 != e2

    def test_equality_non_envelope(self) -> None:
        """Comparison with non-A2AEnvelope returns NotImplemented."""
        env = A2AEnvelope(
            source_agent="orch",
            target_agent="dev",
            payload={},
        )
        assert env != "not an envelope"
        assert env != 42

    def test_repr(self) -> None:
        """__repr__ includes key fields."""
        env = A2AEnvelope(
            source_agent="orchestrator",
            target_agent="developer",
            payload={"x": 1},
            handoff_id="HOFF-20260601-042",
        )
        r = repr(env)
        assert "HOFF-20260601-042" in r
        assert "orchestrator" in r
        assert "developer" in r
