"""Contract test: canonical escalate-card contract and its single source.

SR-C-06 / W1-T5 established the contract; SR-C-07 / W2-C2 pins it to one
place. The orchestrator rejects any ESCALATE card lacking a categorical
reason and a quantifiable metric. The canonical field schema plus the
mandatory rule now live in exactly one file —
``snippets/agents/escalate-card.md`` — which renders as
``{{ESCALATE_CARD_BLOCK}}`` into every developer-tier template. The
unrendered templates therefore carry no literal card (placeholder +
role-specific lines only), while the rendered golden output must carry
the canonical card verbatim. Every orchestrator description of the
principal gate must name reason + metric (no "task summary + failure
log" only variant left).

Proximity window: the same line. Every gate description is a single
table row / paragraph / list item, so same-line is the natural unit.
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_GENERIC = _ROOT / "agents" / "1-generic"
_SNIPPET = _ROOT / "snippets" / "agents" / "escalate-card.md"
_GOLDEN_DIR = _ROOT / "tests" / "fixtures" / "slimming-golden"
_CANONICAL = ("ESCALATE_REASON", "ESCALATE_METRIC")
_CANONICAL_FIELDS = (
    "STATUS",
    "RESULT",
    "ESCALATE_REASON",
    "ESCALATE_METRIC",
    "RECOMMENDED_TIER",
    "PARTIAL_WORK",
    "NEXT_STEPS",
)
_PLACEHOLDER = "{{ESCALATE_CARD_BLOCK}}"
_MANDATORY_RULE = "MANDATORY (issue #346)"
_GATE_MARKERS = re.compile(r"task summary|failure log", re.IGNORECASE)
# Old inline card keyword — a standalone `ESCALATE` line marks a second,
# non-canonical card body that must not survive next to the placeholder.
_OLD_CARD_KEYWORD = re.compile(r"^ESCALATE$", re.MULTILINE)

# Unrendered tier template -> the role-specific lines that must accompany the
# canonical placeholder. The generic card schema carries no tier values, so
# each tier documents its own next-tier values and extra fields.
_TIER_LINES: dict[str, tuple[str, ...]] = {
    "junior-developer.md": (
        "RECOMMENDED_TIER for this tier: developer | senior-developer",
        "FINDINGS:",
    ),
    "developer.md": (
        "RECOMMENDED_TIER for this tier: <junior-developer|developer|senior-developer>",
    ),
    "senior-developer.md": (
        "RECOMMENDED_TIER for this tier: principal-developer",
        "TASK_SUMMARY:",
        "FAILURE_LOG:",
    ),
    "se-developer.md": (
        "RECOMMENDED_TIER for this tier: se-senior-developer",
        "LEAF_ID:",
        "REQ_ID:",
        "FINDINGS:",
    ),
    "se-junior-developer.md": (
        "RECOMMENDED_TIER for this tier: se-developer | se-senior-developer",
        "LEAF_ID:",
        "REQ_ID:",
        "FINDINGS:",
    ),
}


def _read(name: str) -> str:
    return (_GENERIC / name).read_text(encoding="utf-8")


def _escalate_blocks(text: str) -> list[str]:
    """Return every fenced block that contains `STATUS: escalate`."""
    return [
        block
        for block in re.findall(r"```\n(.*?)```", text, re.DOTALL)
        if "STATUS: escalate" in block
    ]


def _field_names(text: str) -> set[str]:
    return set(re.findall(r"^([A-Z_]+):", text, re.MULTILINE))


def test_snippet_defines_canonical_fields_and_mandatory_rule():
    snippet = _SNIPPET.read_text(encoding="utf-8")
    assert _CANONICAL[0] + ":" in snippet
    assert _CANONICAL[1] + ":" in snippet
    assert _MANDATORY_RULE in snippet
    missing = [f for f in _CANONICAL_FIELDS if f not in _field_names(snippet)]
    assert missing == [], f"snippet lacks canonical fields: {missing}"
    assert _PLACEHOLDER not in snippet, "snippet must not reference itself"


def test_tier_templates_reference_snippet_without_literal_card():
    """Each tier template inlines the snippet and keeps only role lines."""
    problems: list[str] = []
    for name, role_lines in _TIER_LINES.items():
        text = _read(name)
        if _PLACEHOLDER not in text:
            problems.append(f"{name}: missing {_PLACEHOLDER}")
        for line in role_lines:
            if line not in text:
                problems.append(f"{name}: role line {line!r} missing")
        if _escalate_blocks(text):
            problems.append(f"{name}: literal STATUS: escalate card still present")
        if _OLD_CARD_KEYWORD.search(text):
            problems.append(f"{name}: standalone ESCALATE card keyword still present")
    assert problems == [], "\n".join(problems)


def test_roles_keep_only_declared_lines_after_placeholder():
    """No undeclared canonical field literal survives outside the snippet."""
    problems: list[str] = []
    for name in _TIER_LINES:
        for field in _CANONICAL:
            literal = f"\n{field}: "
            if literal in _read(name):
                problems.append(f"{name}: literal {field} card line still present")
    assert problems == [], "\n".join(problems)


def test_rendered_goldens_carry_canonical_card():
    """Rendered output of the active tiers carries the canonical card.

    The golden corpus covers the 58 active roles; the ``se-*`` tiers are
    inactive in this repo and have no golden (their contract is pinned by
    ``test_tier_templates_reference_snippet_without_literal_card``).
    """
    checked = 0
    for name in _TIER_LINES:
        golden_path = _GOLDEN_DIR / name
        if not golden_path.exists():
            continue
        text = golden_path.read_text(encoding="utf-8")
        checked += 1
        for field in ("ESCALATE_REASON:", "ESCALATE_METRIC:"):
            assert field in text, f"golden {name} lacks {field}"
        assert _MANDATORY_RULE in text, f"golden {name} lacks mandatory rule"
    assert checked == 3, f"expected 3 golden-covered tiers, found {checked}"


def _render_template(path: Path) -> str:
    """Render one (platform) template the way the sync pipeline does."""
    from scripts.lib.agent_sync import compose_agent
    from scripts.lib.config import build_variables, load_config
    from scripts.lib.frontmatter import extract_frontmatter_field
    from scripts.lib.log import SyncLog
    from scripts.lib.variables import strip_inactive_conditional_blocks, substitute

    config = load_config(_ROOT / ".meta-config" / "project.yaml")
    variables, _warnings = build_variables(config, _ROOT, Path("/tmp/am-escalate-render"))
    log = SyncLog()
    text = path.read_text(encoding="utf-8")
    extends = extract_frontmatter_field(text, "extends")
    if extends:
        text = compose_agent(_ROOT / "agents" / extends, text, log)
    rendered = substitute(text, variables, str(path), log)
    return strip_inactive_conditional_blocks(rendered, variables)


def test_homeassistant_override_satisfies_intake_rule():
    """AC SR-C-07: the platform override's card carries reason AND metric."""
    override = _ROOT / "agents" / "2-platform" / "homeassistant-developer.md"
    source = override.read_text(encoding="utf-8")
    assert _PLACEHOLDER in source, "override does not inline the canonical card"
    assert "ESCALATE_REASON: <short>" not in source, "metric-less card literal remains"
    rendered = _render_template(override)
    card = next(
        (b for b in re.findall(r"```\n(.*?)```", rendered, re.DOTALL)
         if "STATUS: escalate" in b),
        "",
    )
    assert "ESCALATE_REASON:" in card, "rendered override card lacks ESCALATE_REASON"
    assert "ESCALATE_METRIC:" in card, "rendered override card lacks ESCALATE_METRIC"
    assert _MANDATORY_RULE in rendered
    assert "RECOMMENDED_TIER for this tier: <junior-developer|developer|senior-developer>" in rendered


def _gate_lines_without_reason_metric(text: str) -> list[str]:
    bad = []
    for line in text.splitlines():
        if not _GATE_MARKERS.search(line):
            continue
        low = line.lower()
        if "reason" not in low or "metric" not in low:
            bad.append(line.strip())
    return bad


def test_orchestrator_gate_descriptions_name_reason_and_metric():
    text = _read("orchestrator.md")
    assert _GATE_MARKERS.search(text), "gate description vanished"
    assert _gate_lines_without_reason_metric(text) == []


def test_senior_escalation_prose_names_reason_and_metric():

    text = _read("senior-developer.md")
    bad = [
        line for line in _gate_lines_without_reason_metric(text)
        if "Compile a failure log" not in line
    ]
    assert bad == []
