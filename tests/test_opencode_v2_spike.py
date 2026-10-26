"""Structure contract for the C0 spike result document (issue #1007, AC-C1).

Plan: ``docs/plans/2026-10-22-opencode-v2-support-plan.md`` Task 1 (C0.1) and
Task 3a (AC-C2 guard test).
Spec: ``docs/specs/2026-10-22-opencode-v2-support-spec.md`` 3.6 / AC-C1 / AC-C2.

The tests are document checks: no network, no runtime probing. The one
exception is ``test_ac_c2_gate_fallback_invariants``, which additionally reads
the resolved provider registry/capabilities and — only in the NO-GO case —
exercises the capability-gated plugin writer against ``tmp_path``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.log import SyncLog
from lib.providers import (
    SUPPORTED_PLUGIN_PROTOCOLS,
    load_provider_capabilities,
    load_providers_config,
    provider_runtime_gate_tier,
)
from lib.runtime_gate import sync_runtime_gate_plugins

REPO_ROOT = _REPO_ROOT

SPIKE = Path("docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md")
SPEC = Path("docs/specs/2026-10-22-opencode-v2-support-spec.md")

MARKERS = ("VERIFIED", "DOKU", "UNVERIFIED")
MARKER_TOKEN_RE = re.compile(r"\b(VERIFIED|DOKU|UNVERIFIED)\b")
Q_HEADING_RE = re.compile(r"(?m)^## Q([1-6])\b")
H2_RE = re.compile(r"(?m)^## ")
VERDICT_C3_RE = re.compile(r"(?m)^VERDICT-C3: (GO|NO-GO)$")
VERDICT_FIELDS_RE = re.compile(r"(?m)^VERDICT-FIELDS: (CONFIRMED|AMEND)$")
PROBES_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?Proben:\s*(\d+)\s*$")
SOURCES_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?Quellen:\s*(\d+)\s*$")
AMENDMENT_B1_HEADING_RE = re.compile(
    r"(?mi)^#{1,6}\s.*\bAmendment\s+B1\b"
)

Q5_KEYS = ("timeout", "oauth", "disabled", "system", "variant")
Q6_KEYS = (
    "experimental.subagent_depth",
    "experimental.todo",
    "providers",
    "agents.title.model",
    "cli.json",
)


def _read(rel_path: Path) -> str:
    path = REPO_ROOT / rel_path
    assert path.is_file(), f"missing document: {rel_path.as_posix()}"
    return path.read_text(encoding="utf-8")


def _read_spike() -> str:
    return _read(SPIKE)


#: Provider entry whose v2 surface the gate fallback is about. Test-side
#: literal: the fixture exercises that concrete surface, not a dispatch branch.
_V2_PROVIDER = "Opencode"
_V2_PROJECT_CONFIG = {
    "provider-options": {_V2_PROVIDER: {"surface-version": "v2"}}
}

#: Registry keys that Task 18 adds only after ``VERDICT-C3: GO`` (Spec 3.1).
_C3_REGISTRY_KEYS = ("surface-plugin-protocols", "surface-has-plugins")


def _c3_verdict() -> str:
    """Return the single ``VERDICT-C3`` value of the spike document."""
    values = VERDICT_C3_RE.findall(_read(SPIKE))
    assert len(values) == 1, (
        f"expected exactly one 'VERDICT-C3:' line in {SPIKE.as_posix()}, "
        f"found {len(values)}"
    )
    return values[0]


def _resolved_v2_provider() -> tuple[dict, dict]:
    """Resolve the v2 project's provider entry and its declared capabilities."""
    providers = load_providers_config(REPO_ROOT, _V2_PROJECT_CONFIG)
    entry = providers.get(_V2_PROVIDER)
    assert isinstance(entry, dict), f"registry has no {_V2_PROVIDER!r} entry"
    caps = load_provider_capabilities(REPO_ROOT).get(_V2_PROVIDER)
    assert isinstance(caps, dict), (
        f"capabilities registry has no {_V2_PROVIDER!r} entry"
    )
    return entry, caps


def _q_sections(text: str) -> dict[int, str]:
    """Return the text of each ``## Qn`` section, up to the next level-2 heading."""
    sections: dict[int, str] = {}
    for match in Q_HEADING_RE.finditer(text):
        number = int(match.group(1))
        next_h2 = H2_RE.search(text, match.start() + 1)
        end = next_h2.start() if next_h2 else len(text)
        sections[number] = text[match.start() : end]
    return sections


def _key_marker_line_re(key: str) -> re.Pattern[str]:
    return re.compile(
        r"(?m)^\s*(?:[-*]\s*)?" + re.escape(key) + r":\s*(VERIFIED|DOKU|UNVERIFIED)\b"
    )


def test_spike_doc_exists() -> None:
    """AC-C1: the spike result document exists and is not empty."""
    path = REPO_ROOT / SPIKE
    assert path.is_file(), f"missing spike document: {SPIKE.as_posix()}"
    assert path.read_text(encoding="utf-8").strip(), (
        f"spike document is empty: {SPIKE.as_posix()}"
    )


def test_q1_to_q6_sections_present() -> None:
    """AC-C1 / Spec 3.6: exactly one ``## Q1`` ... ``## Q6`` heading each."""
    text = _read_spike()
    numbers = [int(m.group(1)) for m in Q_HEADING_RE.finditer(text)]
    assert len(numbers) == 6, f"expected 6 Q headings, found {len(numbers)}: {numbers}"
    assert sorted(numbers) == [1, 2, 3, 4, 5, 6], f"expected Q1..Q6 once each, got {numbers}"


def test_each_answer_has_marker_and_source() -> None:
    """AC-C1 / Spec 3.6: each Q section carries a marker and a ``Quelle:`` line."""
    sections = _q_sections(_read_spike())
    assert sorted(sections) == [1, 2, 3, 4, 5, 6], (
        f"expected sections Q1..Q6, found {sorted(sections)}"
    )
    for number in range(1, 7):
        body = sections[number]
        markers = MARKER_TOKEN_RE.findall(body)
        assert markers, f"Q{number}: no evidence marker (VERIFIED/DOKU/UNVERIFIED)"
        assert re.search(r"(?m)^\s*(?:[-*]\s*)?Quelle:", body), (
            f"Q{number}: missing 'Quelle:' line"
        )


def test_q5_q6_marker_per_key() -> None:
    """Spec 3.6 Q5/Q6: every verified field/key carries its own marker line."""
    sections = _q_sections(_read_spike())
    for number in (5, 6):
        assert number in sections, f"missing section Q{number}"

    for key in Q5_KEYS:
        assert _key_marker_line_re(key).search(sections[5]), (
            f"Q5: missing marker line '{key}: VERIFIED|DOKU|UNVERIFIED'"
        )
    for key in Q6_KEYS:
        assert _key_marker_line_re(key).search(sections[6]), (
            f"Q6: missing marker line '{key}: VERIFIED|DOKU|UNVERIFIED'"
        )


def test_ac_c1_verdict_lines_exactly_once() -> None:
    """AC-C1: each verdict line occurs exactly once in the spike document."""
    text = _read_spike()
    c3 = VERDICT_C3_RE.findall(text)
    fields = VERDICT_FIELDS_RE.findall(text)
    assert len(c3) == 1, f"expected exactly one 'VERDICT-C3:' line, found {len(c3)}"
    assert len(fields) == 1, (
        f"expected exactly one 'VERDICT-FIELDS:' line, found {len(fields)}"
    )


def test_measure_budget_respected() -> None:
    """Spec 3.6 budget: at most 3 probes and 5 sources per question."""
    sections = _q_sections(_read_spike())
    for number in range(1, 7):
        assert number in sections, f"missing section Q{number}"
        body = sections[number]

        probes = [int(value) for value in PROBES_RE.findall(body)]
        sources = [int(value) for value in SOURCES_RE.findall(body)]
        assert probes, f"Q{number}: missing 'Proben: <n>' line"
        assert sources, f"Q{number}: missing 'Quellen: <n>' line"
        assert max(probes) <= 3, f"Q{number}: probe budget exceeded ({probes} > 3)"
        assert max(sources) <= 5, f"Q{number}: source budget exceeded ({sources} > 5)"


def test_ac_c2_gate_fallback_invariants(tmp_path: Path) -> None:
    """AC-C2: the gate fallback invariants hold for both C3 verdicts.

    The verdict is read from the spike document, never hard-coded. In the
    NO-GO case the permission-tier fallback is verified end-to-end on a v2
    project fixture. In the GO case (current verdict) the full equivalence of
    AC-C2 is asserted: the C3 registry keys are present **exactly when** the
    verdict is GO. C0 shipped only the implication "keys present => GO"; Task
    19 sharpens it to "present <=> GO", so a registry that loses the keys while
    the verdict stays GO fails just like keys without a GO verdict. The
    equivalence is GLOBAL: it is evaluated for every registry entry that
    declares one of the two keys (QA-D-04), not only for the v2 fixture below.
    """
    verdict = _c3_verdict()
    pc, caps = _resolved_v2_provider()

    # Non-vacuity anchor: the fixture really resolves the v2 surface.
    assert pc.get("surface-version") == "v2"
    assert pc["mcp-config"]["format"] == "opencode-json-v2"
    assert pc["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"

    # AC-C2 equivalence (Task 19): C3 keys present <=> verdict is GO. The keys
    # are both-or-none registry data, so a partial set is a contract violation
    # under either verdict — the expected presence is compared as a list.
    # QA-D-04: ``VERDICT-C3`` is GLOBAL, so the equivalence is checked for EVERY
    # registry entry that declares one of the two keys, not just this fixture's
    # provider. A second entry that carries only half the pair (or that keeps
    # the keys under a NO-GO verdict) must fail as loudly as this one.
    expected_keys = list(_C3_REGISTRY_KEYS) if verdict == "GO" else []
    present_keys = [key for key in _C3_REGISTRY_KEYS if key in pc]
    declaring = {
        name: [key for key in _C3_REGISTRY_KEYS if key in entry]
        for name, entry in load_providers_config(REPO_ROOT).items()
        if isinstance(entry, dict) and any(key in entry for key in _C3_REGISTRY_KEYS)
    }
    if verdict == "GO":
        assert declaring, (
            "AC-C2 equivalence violated: VERDICT-C3 is 'GO', so at least one "
            "registry entry must declare the C3 surface keys "
            f"{expected_keys!r}, found none"
        )
    for name, entry_keys in declaring.items():
        assert entry_keys == expected_keys, (
            f"AC-C2 equivalence violated for provider {name!r}: VERDICT-C3 is "
            f"{verdict!r}, so the registry must declare the C3 surface keys "
            f"{expected_keys!r}, found {entry_keys!r}"
        )
    assert present_keys == expected_keys, (
        f"AC-C2 equivalence violated: VERDICT-C3 is {verdict!r}, so the registry "
        f"must declare the C3 surface keys {expected_keys!r}, "
        f"found {present_keys!r}"
    )

    if verdict != "NO-GO":
        return

    # --- VERDICT-C3: NO-GO — the Permissions-Tier fallback is the contract ---
    assert not present_keys, (
        f"NO-GO verdict but the registry declares C3 keys: {present_keys}"
    )
    assert provider_runtime_gate_tier(pc, caps) == "permission"
    assert pc.get("has_plugins") is False, (
        "NO-GO fallback requires the resolved has_plugins flag to stay false"
    )
    assert caps.get("runtime_gate") == "permission", (
        "config/provider-capabilities.yaml must keep runtime_gate: permission"
    )
    assert SUPPORTED_PLUGIN_PROTOCOLS == {"opencode-plugin-js"}, (
        "NO-GO fallback must not add a v2 plugin protocol to the supported set"
    )

    # AC-C2 asks for "a sync creates no file under .opencode/plugins/". A full
    # sync.py run is not needed to prove this: the plugin artifact is written
    # exclusively by sync_runtime_gate_plugins, gated on the resolved
    # has_plugins flag (sync_pipeline.py:1303). Exercising that writer against
    # tmp_path is the cheap, side-effect-free form of the same assertion.
    log = SyncLog()
    sync_runtime_gate_plugins(
        REPO_ROOT,
        tmp_path,
        {},
        log,
        dry_run=False,
        provider=_V2_PROVIDER,
        provider_config={_V2_PROVIDER: pc},
    )
    plugin_dir = tmp_path / str(pc.get("plugin_dir") or ".opencode/plugins")
    written = sorted(p.name for p in plugin_dir.iterdir()) if plugin_dir.is_dir() else []
    assert written == [], f"NO-GO fallback wrote plugin artifacts: {written}"

    assert "Fallback = Permissions-Tier" in _read(SPIKE), (
        "NO-GO verdict requires the spike document to state "
        "'Fallback = Permissions-Tier'"
    )


def test_verdict_consequences_recorded() -> None:
    """Spec 3.6: AMEND/NO-GO requires an ``Amendment B1`` heading in the spec."""
    text = _read_spike()
    c3 = VERDICT_C3_RE.findall(text)
    fields = VERDICT_FIELDS_RE.findall(text)

    needs_amendment = (fields and fields[0] == "AMEND") or (c3 and c3[0] == "NO-GO")
    if not needs_amendment:
        return

    spec_text = _read(SPEC)
    assert AMENDMENT_B1_HEADING_RE.search(spec_text), (
        "spike verdict requires consequences, but the spec has no "
        "'Amendment B1' heading"
    )
