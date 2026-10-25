"""AC-01: no system temp literal in agent templates.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md`` AC-01,
ADR-06 (WARNING, not a hard exit) and ADR-14/AC-39 (allowlist schema).
The guard scans ``agents/**/*.md`` with the exact AC-01 pattern and only
suppresses a hit when a *complete* allowlist entry matches both path and line
text. An entry without ``reason`` (or with an unsupported field such as
``expires``) suppresses nothing — that is the forward-compatible shape Task 22
hardens; the consistency check owns the WARNING side, this guard stays
assertion-based.

Run: python3 -m pytest tests/test_temp_literals.py -q
"""

import fnmatch
import re
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AGENTS_ROOT = _REPO_ROOT / "agents"
_ALLOWLIST_PATH = _REPO_ROOT / ".meta-config" / "temp-literal-allowlist.yaml"

# Exact AC-01 pattern (case-sensitive, path context). Template/temporary do not
# match because ``/tmp/`` requires the trailing slash and the boundary class
# excludes word characters, dots, underscores and hyphens.
SYSTEM_TEMP_LITERAL_RE = re.compile(r"(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)")

# Q6 / IC-11 / AC-39: path, pattern and reason are mandatory, owner optional,
# ``expires`` is not part of the schema.
_REQUIRED_ENTRY_FIELDS = ("path", "pattern", "reason")
_ALLOWED_ENTRY_FIELDS = frozenset({"path", "pattern", "reason", "owner"})


def load_allowlist():
    """Return the raw allowlist payload (``{"entries": [...]}``)."""
    with _ALLOWLIST_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_allowlist_entries():
    """Return the allowlist entries, tolerating an empty/missing payload."""
    payload = load_allowlist()
    if not isinstance(payload, dict):
        return []
    entries = payload.get("entries")
    return entries if isinstance(entries, list) else []


def entry_is_valid(entry):
    """True only for a complete, supported allowlist entry (AC-39 shape)."""
    if not isinstance(entry, dict):
        return False
    if set(entry) - _ALLOWED_ENTRY_FIELDS:
        return False
    for field in _REQUIRED_ENTRY_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    try:
        re.compile(entry["pattern"])
    except re.error:
        return False
    return True


def entry_suppresses(entry, relpath, line):
    """A complete entry suppresses only its own path (glob) and line (regex)."""
    if not entry_is_valid(entry):
        return False
    if not fnmatch.fnmatch(relpath, entry["path"]):
        return False
    return re.search(entry["pattern"], line) is not None


def collect_hits():
    """Return ``relpath:line: text`` for every unsuppressed literal hit."""
    entries = load_allowlist_entries()
    hits = []
    for path in sorted(_AGENTS_ROOT.rglob("*.md")):
        relpath = path.relative_to(_REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not SYSTEM_TEMP_LITERAL_RE.search(line):
                continue
            if any(entry_suppresses(entry, relpath, line) for entry in entries):
                continue
            hits.append(f"{relpath}:{lineno}: {line.strip()}")
    return hits


def test_no_system_temp_literal_in_agents():
    """AC-01: ``agents/**/*.md`` carries no system temp literal."""
    hits = collect_hits()
    assert not hits, (
        "system temp literal(s) found in agents/** (AC-01, ADR-06). Write to "
        "{{TMP_SINK_PATH}} instead, or declare a complete entry (path, pattern, "
        "reason) in .meta-config/temp-literal-allowlist.yaml:\n" + "\n".join(hits)
    )


def test_allowlist_file_exists_with_entry_list():
    """AC-01/AC-39: the allowlist exists and ``entries`` is a list."""
    assert _ALLOWLIST_PATH.is_file(), f"missing allowlist: {_ALLOWLIST_PATH}"
    payload = load_allowlist()
    assert isinstance(payload, dict), "allowlist root must be a mapping with an 'entries' key"
    assert isinstance(payload.get("entries"), list), "allowlist 'entries' must be a list"


def test_pattern_ignores_words_like_template_and_temporary():
    """AC-01: the pattern matches path context only, not plain words."""
    for word in ("Template", "temporary", "attempt", "my/tmp/x", "tmp/"):
        assert not SYSTEM_TEMP_LITERAL_RE.search(word), word
    for literal in ("/tmp/x.log", "> /tmp/a", "%TEMP%\\x", "C:\\\\Temp\\\\x"):
        assert SYSTEM_TEMP_LITERAL_RE.search(literal), literal


def test_incomplete_allowlist_entry_does_not_suppress():
    """AC-39 shape: reason is mandatory, ``expires`` is not a schema field."""
    line = "docker logs c > /tmp/c.log 2>&1"
    relpath = "agents/1-generic/example.md"
    complete = {"path": relpath, "pattern": r"/tmp/", "reason": "needs a system temp log"}
    assert entry_suppresses(complete, relpath, line)
    assert entry_suppresses(dict(complete, owner="tester"), relpath, line)

    assert not entry_suppresses({k: v for k, v in complete.items() if k != "reason"}, relpath, line)
    assert not entry_suppresses(dict(complete, expires="2026-12-31"), relpath, line)
    assert not entry_suppresses(complete, "agents/1-generic/other.md", line)
