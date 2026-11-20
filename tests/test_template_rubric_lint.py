"""Template rubric lint — Batch 0 Task 1.3 (#885-Ersatz).

Rubric checks R1/R2/R4/R5/R9/R11 from the approved Batch-0 spec (IC-6)
against SOURCE agent templates (agents/1-generic/*.md, review OQ-4). The
template directory is resolved from a provider-agnostic `mappings` parameter
so both source and rendered directories stay supported without provider-name
literals.

STUB PHASE — check bodies are placeholders; run pytest to observe RED.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES = ("R1", "R2", "R4", "R5", "R9", "R11")

CANONICAL_SECTIONS = (
    "Purpose",
    "Boundaries",
    "Parse input",
    "Workflow",
    "Output contract",
    "Don'ts",
    "Escalation",
    "Project context",
    "Language",
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_ISSUE_RE = re.compile(r"Issue\s+#\d+")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")
_DE_MARKERS = frozenset({
    "der", "die", "das", "den", "dem", "des", "und", "oder", "aber",
    "ist", "sind", "war", "waren", "nicht", "kein", "keine", "keinen",
    "mit", "für", "von", "zu", "zum", "zur", "im", "auf", "aus", "bei",
    "durch", "über", "unter", "vor", "nach", "wird", "werden", "wurde",
    "wurden", "hat", "haben", "hatte", "kann", "können", "soll", "sollte",
    "sollten", "muss", "müssen", "darf", "dürfen", "ich", "du", "wir",
    "sie", "sich", "dies", "diese", "dieses", "jeder", "jede", "jedes",
    "aller", "alle", "alles", "etwas", "nichts", "wenn", "dann", "weil",
    "dass", "obwohl", "während", "seit", "bis", "daher", "deshalb",
    "bitte", "hinweis", "anmerkung", "fehler", "siehe", "könnte", "würde",
    "müsste", "einem", "einer", "eines", "einen", "nur", "auch", "noch",
    "bereits", "wieder", "hier", "dort", "sowie", "insbesondere", "gemäß",
    "zwischen", "innerhalb", "beispielsweise",
})

DEFAULT_MAPPINGS: Mapping[str, Mapping] = {
    "source": {"agents_dir": "agents/1-generic", "agent_ext": ".md"},
}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    message: str


# The plan documents the rule IDs (detail plan §4 :95-105) but does NOT
# enumerate which roles currently comply. Per task guidance start with a
# minimal EMPTY allowlist and tighten per batch — never invent role/rule pairs.
ALLOWLIST: dict[str, set[str]] = {rule: set() for rule in RULES}


def resolve_agents_dir(mappings: Mapping[str, Mapping], root: Path = REPO_ROOT) -> Path:
    """Resolve the template directory from a provider-agnostic mappings dict."""
    for spec in mappings.values():
        agents_dir = spec.get("agents_dir")
        if agents_dir:
            return root / str(agents_dir)
    raise ValueError("no agents_dir configured in mappings")


def agent_paths(mappings: Mapping[str, Mapping], root: Path = REPO_ROOT) -> list[Path]:
    """List source template files using only mapping configuration."""
    ext = ".md"
    for spec in mappings.values():
        if spec.get("agent_ext"):
            ext = str(spec["agent_ext"])
            break
    directory = resolve_agents_dir(mappings, root)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if p.is_file() and p.name.endswith(ext))


def _frontmatter_and_body(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    return "", text


def _description(frontmatter: str) -> str | None:
    for line in frontmatter.splitlines():
        match = re.match(r"^description:\s*(.*)$", line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value
    return None


def _headings(body: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line in body.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            result.append((len(match.group(1)), match.group(2).strip()))
    return result


def check_r1(text: str, path: str = "") -> list[Finding]:
    """R1: frontmatter description length only (max 160 chars)."""
    frontmatter, _ = _frontmatter_and_body(text)
    description = _description(frontmatter)
    if description is None:
        return [Finding("R1", path, "missing frontmatter description")]
    if len(description) > 160:
        return [Finding("R1", path, f"description has {len(description)} chars (max 160)")]
    return []


def check_r2(text: str, path: str = "") -> list[Finding]:
    """R2: canonical 'Boundaries' section present (review: section-only)."""
    _, body = _frontmatter_and_body(text)
    names = [name for _, name in _headings(body)]
    if "Boundaries" in names:
        return []
    legacy = [name for name in names if name.lower() in {"grenzen", "does not", "does-not"}]
    if legacy:
        return [Finding("R2", path, f"non-canonical Boundaries section: {legacy[0]!r}")]
    return [Finding("R2", path, "missing canonical 'Boundaries' section")]


def check_r4(text: str, path: str = "") -> list[Finding]:
    """R4: exactly one canonical 'Output contract' section."""
    _, body = _frontmatter_and_body(text)
    names = [name for _, name in _headings(body)]
    canonical = [name for name in names if name == "Output contract"]
    legacy_variants = {"return", "json output schema", "output-contract", "output schema"}
    legacy = [name for name in names if name.lower() in legacy_variants]
    findings: list[Finding] = []
    if len(canonical) != 1:
        findings.append(
            Finding("R4", path, f"expected 1 'Output contract' section, found {len(canonical)}")
        )
    if legacy:
        findings.append(Finding("R4", path, f"non-canonical output section: {legacy[0]!r}"))
    return findings


def check_r5(text: str, path: str = "") -> list[Finding]:
    """R5: at most 7 bullets in the 'Don'ts' section."""
    _, body = _frontmatter_and_body(text)
    lines = body.splitlines()
    start = None
    level = None
    for index, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match and match.group(2).strip() == "Don'ts":
            start, level = index + 1, len(match.group(1))
            break
    if start is None:
        return [Finding("R5", path, "missing canonical \"Don'ts\" section")]
    bullets = 0
    for line in lines[start:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= (level or 6):
            break
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            bullets += 1
    if bullets > 7:
        return [Finding("R5", path, f"Don'ts has {bullets} bullets (max 7)")]
    return []


def check_r9(text: str, path: str = "") -> list[Finding]:
    """R9: no 'Issue #N' in the body outside HTML comments."""
    _, body = _frontmatter_and_body(text)
    stripped = _HTML_COMMENT_RE.sub("", body)
    matches = _ISSUE_RE.findall(stripped)
    if matches:
        return [Finding("R9", path, f"Issue reference in body: {matches[0]!r}")]
    return []


def check_r11(text: str, path: str = "") -> list[Finding]:
    """R11: German marker quote below 5 percent."""
    _, body = _frontmatter_and_body(text)
    words = _WORD_RE.findall(body)
    if not words:
        return []
    de_count = sum(1 for word in words if word.lower() in _DE_MARKERS)
    ratio = de_count / len(words)
    if ratio >= 0.05:
        return [Finding("R11", path, f"DE-marker quote {ratio:.1%} (max 5%)")]
    return []


CHECKS = {
    "R1": check_r1,
    "R2": check_r2,
    "R4": check_r4,
    "R5": check_r5,
    "R9": check_r9,
    "R11": check_r11,
}


# --- Unit tests (TDD core: must be RED with stubs, GREEN after implementation) ---


def test_r1_rejects_long_description():
    text = "---\ndescription: \"" + "x" * 161 + "\"\n---\nbody"
    assert check_r1(text)


def test_r1_accepts_short_description():
    assert check_r1("---\ndescription: \"short\"\n---\nbody") == []


def test_r1_missing_description_is_finding_not_crash():
    assert check_r1("---\nname: x\n---\nbody")


def test_r2_accepts_canonical_boundaries():
    assert check_r2("## Boundaries\n- Does not X") == []


def test_r2_rejects_missing_boundaries():
    assert check_r2("## Workflow\nstep")


def test_r2_rejects_legacy_name():
    assert check_r2("## Grenzen\n- X")


def test_r4_accepts_exactly_one_canonical():
    assert check_r4("## Output contract\n`{}`") == []


def test_r4_rejects_two_canonical():
    assert check_r4("## Output contract\na\n## Output contract\nb")


def test_r4_rejects_legacy_name():
    assert check_r4("## Return\n`{}`")


def test_r5_accepts_seven_bullets():
    body = "## Don'ts\n" + "\n".join(f"- item {index}" for index in range(7))
    assert check_r5(body) == []


def test_r5_rejects_eight_bullets():
    body = "## Don'ts\n" + "\n".join(f"- item {index}" for index in range(8))
    assert check_r5(body)


def test_r9_ignores_issue_in_html_comment():
    assert check_r9("Body <!-- Issue #123 -->") == []


def test_r9_rejects_issue_in_body():
    assert check_r9("See Issue #123 for context.")


def test_r11_accepts_english():
    assert check_r11(" ".join(["the quick brown fox jumps over the lazy dog"] * 5)) == []


def test_r11_rejects_german_heavy():
    assert check_r11(" ".join(["der die das und ist nicht mit für wird"] * 10))


def test_allowlist_keys_cover_all_rules():
    assert set(ALLOWLIST) == set(RULES)


def test_mappings_resolve_absolute_directory(tmp_path):
    mappings = {"any-key": {"agents_dir": str(tmp_path), "agent_ext": ".md"}}
    assert resolve_agents_dir(mappings) == tmp_path
    assert agent_paths(mappings) == []


# --- Parametrized ratchet over all source roles x rules (start state) ---


def _build_params(mappings: Mapping[str, Mapping]) -> list[pytest.ParameterSet]:
    params: list[pytest.ParameterSet] = []
    for path in agent_paths(mappings):
        text = path.read_text(encoding="utf-8")
        for rule in RULES:
            marks = []
            if path.stem not in ALLOWLIST.get(rule, set()):
                marks.append(
                    pytest.mark.xfail(
                        strict=False,
                        reason="Batch-0 allowlist, tighten per batch",
                    )
                )
            params.append(
                pytest.param(
                    rule,
                    path.stem,
                    str(path),
                    text,
                    marks=marks,
                    id=f"{rule}:{path.stem}",
                )
            )
    return params


_RUBRIC_PARAMS = _build_params(DEFAULT_MAPPINGS)


@pytest.mark.parametrize("rule,stem,path,text", _RUBRIC_PARAMS)
def test_rubric_rule(rule, stem, path, text):
    findings = CHECKS[rule](text, path)
    assert findings == [], findings
