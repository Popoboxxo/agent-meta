"""IC-35 / AC-81 / AC-89: runtime config reader registry.

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 20 and
``docs/specs/2026-10-11-context-profiles-spec.md`` IC-35 (Rev 3.1), AC-81
(registry part) and AC-89 (credential patterns).

The registry ``config/runtime-config-readers.yaml`` documents which
``.meta-config/project.yaml`` keys are consumed at *runtime* by hooks/scripts
(outside the sync render path) and which paths are credentials. This test file
covers:

(a) every ``evidence`` anchor is symbolic (``<path>#<prefix>:<key>``) and
    appears exactly once in the reader source on the line that actually reads
    the key -- a line-number anchor, a missing/duplicate marker, a marker in
    another file or a marker for another key is an error (Review M7);
(b) the completeness ratchet over ``hooks/**/*.sh`` **and** top-level
    ``scripts/*.py`` with a reasoned exception list that may only shrink;
(c) the credential patterns against a positive/negative list;
(d) the registry shape (version, reader fields, unique keys).
"""
import re
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.secrets import scan_for_secrets  # noqa: E402

REGISTRY_PATH = _ROOT / "config" / "runtime-config-readers.yaml"
HOOKS_ROOT = _ROOT / "hooks"
SCRIPTS_ROOT = _ROOT / "scripts"

# Machine-readable exception reasons (AC-89 / spec IC-35 Rev. 3.1).
SYNC_RENDER_PATH = "sync-render-path"       # sync/render path whose effect L0 covers
NO_RUNTIME_EFFECT = "no-runtime-effect"     # maintenance/migration tool without runtime effect
_REASONS = {SYNC_RENDER_PATH, NO_RUNTIME_EFFECT}

# --- Ratchet start list (may only SHRINK) -----------------------------------
# Plan Rev. 3.1 start classification minus the now-registered files
# (`admin-server.py`, `lifecycle_check.py`). Frozen on purpose: a new
# unregistered reader must be registered (or a reviewed exception added here),
# never silently appended.
PY_EXCEPTION_START = {
    "scripts/consistency-check.py": NO_RUNTIME_EFFECT,
    "scripts/gen_routing_llm_eval_catalog.py": NO_RUNTIME_EFFECT,
    "scripts/migrate-config.py": NO_RUNTIME_EFFECT,
    "scripts/migrate-plugin-registry.py": NO_RUNTIME_EFFECT,
    "scripts/se-export.py": NO_RUNTIME_EFFECT,
    "scripts/sync.py": SYNC_RENDER_PATH,
    "scripts/viz-logger.py": NO_RUNTIME_EFFECT,
    "scripts/viz-report.py": NO_RUNTIME_EFFECT,
}

# Hook hits that are not runtime value readers: the release-gate values are
# baked in at sync time (hook_common.sh:214-217, L0-covered) and the remaining
# references are comments / enablement decisions rendered by the sync.
HOOK_EXCEPTION_START = {
    "hooks/1-generic/lib/hook_common.sh": SYNC_RENDER_PATH,
    "hooks/1-generic/sync-on-config-change.sh": SYNC_RENDER_PATH,
    "hooks/1-generic/pre-release-check.sh": SYNC_RENDER_PATH,
    "hooks/1-generic/release-gates/action-pin-validation.sh": SYNC_RENDER_PATH,
    "hooks/1-generic/release-gates/artifact-freshness.sh": SYNC_RENDER_PATH,
    "hooks/1-generic/release-gates/docker-image-scan.sh": SYNC_RENDER_PATH,
}


# --------------------------------------------------------------------- helpers

def _registry():
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def _reader_keys():
    return [str(entry["key"]) for entry in _registry()["readers"]]


def _registered_reader_files():
    """Repo-relative reader source paths declared in the registry."""
    return {str(entry["reader"]) for entry in _registry()["readers"]}


# Symbolic anchor: ``<path>#<prefix>:<key>``, e.g.
# ``.claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND``.
# A line-number anchor (``<path>:<line>``) is rejected outright: it drifts with
# every edit and stays green when the referenced line merely *mentions* the key
# somewhere else (Review M7, ``:1119`` pointed at an unrelated ``echo`` line).
_ANCHOR_RE = re.compile(r"^(?P<path>[^#\s]+)#(?P<anchor>[a-z][a-z0-9-]*:[^\s#]+)$")
_LEGACY_LINE_ANCHOR_RE = re.compile(r"^(?P<path>[^#\s]+):(?P<line>\d+)(?:-(?P<end>\d+))?$")

READER_PREFIX = "runtime-reader"
CREDENTIAL_PREFIX = "credential-key"
# The marker must sit on a real config read, not on prose that happens to name
# the key (``echo "Set variables.TEST_COMMAND ..."``). Shell + Python idioms.
_READ_CALL_RE = re.compile(
    r"\bread_config_var\b|\.get\s*\(|\.get\[|\bsafe_load\s*\(|\bload_config\s*\(")

# `yaml.safe_load`/`load_config`/`load_yaml_file` on a `project.yaml` reference.
_LOAD_MARKERS = ("load_config(", "_load_config(", "load_yaml_file(", "yaml.safe_load(")
_PROJECT_CONFIG_RE = re.compile(r"project\.yaml")

# `config.get("<key>")` / `config["<key>"]` on a name that looks like a config
# dict. Keys are top-level (no dot) for the ratchet's purposes.
_CONFIG_VAR = re.compile(r"config|cfg")
_KEY_GET_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.get\(\s*[\"']([A-Za-z0-9_-]+)[\"']")
_KEY_SUB_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*[\"']([A-Za-z0-9_-]+)[\"']\s*\]")

# Shell readers: a hook that references the config file or the shared helper.
_SHELL_READER_RE = re.compile(r"project\.yaml|read_config_var")


def _rel(path, root):
    """Path relative to the repo when possible, else relative to *root*."""
    try:
        return path.resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return path.relative_to(root).as_posix()


def _shell_reader_hits(root):
    """Repo-relative paths of ``*.sh`` files that read the project config."""
    hits = set()
    for path in sorted(Path(root).rglob("*.sh")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if _SHELL_READER_RE.search(text):
            hits.add(_rel(path, root))
    return hits


def _loads_project_yaml(text):
    return bool(_PROJECT_CONFIG_RE.search(text)) and any(m in text for m in _LOAD_MARKERS)


def _top_level_keys(text):
    keys = set()
    for var, key in _KEY_GET_RE.findall(text) + _KEY_SUB_RE.findall(text):
        if _CONFIG_VAR.search(var):
            keys.add(key)
    return keys


def _py_reader_hits(root):
    """``{repo-relative path: top-level keys read}`` for top-level ``scripts/*.py``."""
    hits = {}
    for path in sorted(Path(root).glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        keys = _top_level_keys(text)
        if _loads_project_yaml(text) and keys:
            hits[_rel(path, root)] = keys
    return hits


def _ratchet_violations(hits, registered, exceptions):
    """Hit paths that are neither registered readers nor reasoned exceptions."""
    return sorted(str(h) for h in hits if h not in registered and h not in exceptions)


# ------------------------------------------------------ (a) symbolic anchors

def _marker_re(anchor):
    """Regex for the comment marker of *anchor* (the whole id, never a prefix)."""
    return re.compile(r"#\s*" + re.escape(anchor) + r"(?![A-Za-z0-9_.-])")


def _anchor_errors_for_entry(root, where, key, evidence, prefix, source_rel,
                             require_read):
    """All anchor errors of one registry entry (empty list = healthy).

    Fails hard on: a line-number anchor, an anchor for another key, a missing
    source file, a missing marker, a duplicated marker, a marker that sits on a
    line other than the key read (or on prose), so the M7 failure class
    ("line mentions the key somewhere") can never pass again.
    """
    evidence = str(evidence)
    if _LEGACY_LINE_ANCHOR_RE.match(evidence):
        return [
            f"{where}: line-number anchor {evidence!r} is not accepted; "
            f"use '<path>#{prefix}:{key}'"
        ]

    match = _ANCHOR_RE.match(evidence)
    if not match:
        return [
            f"{where}: unparseable evidence {evidence!r}; "
            f"expected '<path>#{prefix}:{key}'"
        ]

    expected = f"{prefix}:{key}"
    anchor = match["anchor"]
    if anchor != expected:
        return [
            f"{where}: anchor {anchor!r} belongs to another key; "
            f"expected {expected!r}"
        ]

    source = Path(root) / str(source_rel)
    if not source.is_file():
        return [f"{where}: source file {source_rel} is missing"]

    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    marker = _marker_re(anchor)
    hits = [number for number, line in enumerate(lines, start=1) if marker.search(line)]
    if not hits:
        return [f"{where}: marker '# {anchor}' is missing in {source_rel}"]
    if len(hits) > 1:
        return [
            f"{where}: marker '# {anchor}' is ambiguous in {source_rel} "
            f"(lines {hits}); a marker must anchor exactly one line"
        ]

    if not require_read:
        # Credentials have no read expression; the file must at least name the
        # key (outside the marker comment itself) so a stale path cannot point
        # at an unrelated file.
        text = "\n".join(marker.sub("", line) for line in lines)
        tail = key.split(".")[-1]
        if key not in text and tail not in text:
            return [
                f"{where}: {source_rel} neither names {key!r} nor its leaf "
                f"{tail!r}"
            ]
        return []

    line = lines[hits[0] - 1]
    code = marker.sub("", line)
    tail = key.split(".")[-1]
    if tail not in code:
        return [
            f"{where}: {source_rel}:{hits[0]} does not read key {key!r}: "
            f"{line.strip()!r}"
        ]
    if not _READ_CALL_RE.search(code):
        return [
            f"{where}: {source_rel}:{hits[0]} is prose, not a config read: "
            f"{line.strip()!r}"
        ]
    return []


def _registry_anchor_errors(registry, root):
    """All anchor errors of a registry mapping, resolved against *root*."""
    errors = []
    for entry in registry.get("readers") or []:
        key = str(entry["key"])
        reader = str(entry["reader"])
        evidence = str(entry["evidence"])
        errors.extend(_anchor_errors_for_entry(
            root, f"readers[{key}]", key, evidence, READER_PREFIX, reader,
            require_read=True))
        if "#" in evidence:
            evidence_path = evidence.split("#", 1)[0]
            if Path(evidence_path).name != Path(reader).name:
                errors.append(
                    f"readers[{key}]: evidence path {evidence_path!r} is not a "
                    f"copy of reader {reader!r}")
    for entry in (registry.get("credentials") or {}).get("keys") or []:
        key = str(entry["key"])
        evidence = str(entry["evidence"])
        errors.extend(_anchor_errors_for_entry(
            root, f"credentials.keys[{key}]", key, evidence,
            CREDENTIAL_PREFIX, evidence.split("#", 1)[0], require_read=False))
    return errors


def test_a_registry_anchors_are_unique_key_markers():
    """Every entry resolves to exactly one marker on the line that reads the key."""
    errors = _registry_anchor_errors(_registry(), _ROOT)
    assert errors == [], "\n".join(errors)


# --- negative guards: each failure mode is a hard error, not a warning -------

_READER = "hooks/1-generic/dod-push-check.sh"
_READ_LINE = (
    'TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")'
    '  # runtime-reader:variables.TEST_COMMAND\n'
)
# The M7 fixture: an `echo` line that mentions both `project.yaml` and the key,
# immediately followed by the real read.
_PROSE_THEN_READ = (
    'CONFIG="$PWD/.meta-config/project.yaml"\n'
    'echo "Set variables.TEST_COMMAND in .meta-config/project.yaml"'
    '  # runtime-reader:variables.TEST_COMMAND\n'
    'TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")\n'
)


def _write_source(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _reader_registry(key, evidence, reader=_READER):
    return {"readers": [{"key": key, "reader": reader,
                         "evidence": evidence, "effect": "test"}]}


def test_a_line_number_anchor_is_rejected_even_when_the_line_mentions_the_key(tmp_path):
    """M7 regression: the old ``:1119`` anchor pointed at an ``echo`` line that
    happened to contain ``project.yaml``. That anchor type is now a hard error,
    although the old "mentions the key" predicate would still go green."""
    _write_source(tmp_path, _READER, _PROSE_THEN_READ)
    old_line = _PROSE_THEN_READ.splitlines()[1]
    assert "project.yaml" in old_line and "TEST_COMMAND" in old_line

    errors = _registry_anchor_errors(
        _reader_registry("variables.TEST_COMMAND",
                         ".claude/hooks/dod-push-check.sh:2"),
        tmp_path)
    assert len(errors) == 1
    assert "line-number anchor" in errors[0]


def test_a_marker_on_a_prose_line_is_rejected(tmp_path):
    """Same line, now with a marker: the marker must sit on the read itself."""
    _write_source(tmp_path, _READER, _PROSE_THEN_READ)
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert "is prose, not a config read" in errors[0]


def test_a_missing_marker_is_an_error(tmp_path):
    _write_source(tmp_path, _READER,
                  'TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")\n')
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert "is missing" in errors[0]


def test_a_duplicate_marker_is_an_error(tmp_path):
    _write_source(tmp_path, _READER, _READ_LINE + _READ_LINE)
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert "is ambiguous" in errors[0]


def test_a_marker_in_another_file_does_not_count(tmp_path):
    """The marker must live in the file the registry names as `reader`."""
    _write_source(tmp_path, "hooks/1-generic/other-hook.sh", _READ_LINE)
    _write_source(tmp_path, _READER, "echo no-read-here\n")
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert f"is missing in {_READER}" in errors[0]


def test_a_evidence_path_must_match_the_named_reader(tmp_path):
    _write_source(tmp_path, _READER, _READ_LINE)
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/other-hook.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert "is not a copy of reader" in errors[0]


def test_a_marker_for_another_key_is_an_error(tmp_path):
    _write_source(
        tmp_path, _READER,
        'TEST_TIMEOUT=$(read_config_var "$CONFIG_FILE" "TEST_TIMEOUT")'
        '  # runtime-reader:variables.TEST_TIMEOUT\n')
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_TIMEOUT"),
        tmp_path)
    assert len(errors) == 1
    assert "belongs to another key" in errors[0]


def test_a_marker_on_a_read_of_another_key_is_an_error(tmp_path):
    _write_source(
        tmp_path, _READER,
        'TEST_TIMEOUT=$(read_config_var "$CONFIG_FILE" "TEST_TIMEOUT")'
        '  # runtime-reader:variables.TEST_COMMAND\n')
    errors = _registry_anchor_errors(
        _reader_registry(
            "variables.TEST_COMMAND",
            ".claude/hooks/dod-push-check.sh#runtime-reader:variables.TEST_COMMAND"),
        tmp_path)
    assert len(errors) == 1
    assert "does not read key" in errors[0]


def _credential_registry(key, evidence):
    return {"credentials": {"keys": [{"key": key, "evidence": evidence}]}}


def test_a_credential_marker_is_required(tmp_path):
    _write_source(tmp_path, "scripts/lib/permissions.py", "token = None\n")
    errors = _registry_anchor_errors(
        _credential_registry(
            "admin-ui.token",
            "scripts/lib/permissions.py#credential-key:admin-ui.token"),
        tmp_path)
    assert len(errors) == 1
    assert "is missing" in errors[0]


def test_a_credential_marker_must_point_at_a_file_that_names_the_key(tmp_path):
    _write_source(
        tmp_path, "scripts/lib/unrelated.py",
        "# credential-key:admin-ui.token\n"
        "def nothing_to_do_here():\n"
        "    return 1\n")
    errors = _registry_anchor_errors(
        _credential_registry(
            "admin-ui.token",
            "scripts/lib/unrelated.py#credential-key:admin-ui.token"),
        tmp_path)
    assert len(errors) == 1
    assert "neither names" in errors[0]


# ------------------------------------------------------------ (b) ratchet

def test_b_hook_ratchet_only_registered_readers_or_reasoned_exceptions():
    hits = _shell_reader_hits(HOOKS_ROOT)
    registered = _registered_reader_files()
    violations = _ratchet_violations(hits, registered, HOOK_EXCEPTION_START)
    assert violations == [], f"unregistered hook readers: {violations}"


def test_b_py_ratchet_only_registered_readers_or_reasoned_exceptions():
    hits = set(_py_reader_hits(SCRIPTS_ROOT))
    registered = _registered_reader_files()
    violations = _ratchet_violations(hits, registered, PY_EXCEPTION_START)
    assert violations == [], f"unregistered python readers: {violations}"


def test_b_live_exceptions_are_a_subset_of_the_frozen_start_list():
    """The exception list may only shrink: a live exception not in the frozen
    start list fails the ratchet (someone added a new exception)."""
    hook_hits = _shell_reader_hits(HOOKS_ROOT)
    registered = _registered_reader_files()
    live_hooks = {h for h in hook_hits if h not in registered}
    py_hits = set(_py_reader_hits(SCRIPTS_ROOT))
    live_py = {h for h in py_hits if h not in registered}

    assert live_hooks <= set(HOOK_EXCEPTION_START), (
        f"new hook exceptions not in the frozen start list: {sorted(live_hooks - set(HOOK_EXCEPTION_START))}")
    assert live_py <= set(PY_EXCEPTION_START), (
        f"new python exceptions not in the frozen start list: {sorted(live_py - set(PY_EXCEPTION_START))}")
    for table in (HOOK_EXCEPTION_START, PY_EXCEPTION_START):
        assert all(reason in _REASONS for reason in table.values()), table


def test_b_ratchet_flags_a_new_unregistered_hook_reader(tmp_path):
    root = tmp_path / "hooks"
    root.mkdir()
    (root / "brand-new.sh").write_text(
        'CONFIG="$PWD/.meta-config/project.yaml"\nread_config_var "$CONFIG" "X"\n',
        encoding="utf-8")
    hits = _shell_reader_hits(root)
    assert "brand-new.sh" in hits
    assert _ratchet_violations(hits, set(), set()) == ["brand-new.sh"]


def test_b_ratchet_flags_a_new_unregistered_python_reader(tmp_path):
    (tmp_path / "brand-new.py").write_text(
        "from lib.config import load_config\n"
        "config = load_config('.meta-config/project.yaml')\n"
        "value = config.get('brand-new-key')\n",
        encoding="utf-8")
    hits = _py_reader_hits(tmp_path)
    assert set(hits) == {"brand-new.py"}
    assert hits["brand-new.py"] == {"brand-new-key"}
    assert _ratchet_violations(hits, set(), set()) == ["brand-new.py"]


def test_b_ratchet_accepts_a_registered_reader(tmp_path):
    (tmp_path / "known.py").write_text(
        "from lib.config import load_config\n"
        "config = load_config('.meta-config/project.yaml')\n"
        "value = config.get('known-key')\n",
        encoding="utf-8")
    hits = _py_reader_hits(tmp_path)
    assert _ratchet_violations(hits, {"known.py"}, set()) == []


# ----------------------------------------------- (c) credential patterns

def _path_is_credential(path, registry):
    creds = registry["credentials"]
    for pattern in creds["name_patterns"]:
        for segment in str(path).split("."):
            if re.search(pattern, segment, re.IGNORECASE):
                return True
    for entry in creds["keys"]:
        key = str(entry["key"])
        if str(path) == key or str(path).startswith(key + "."):
            return True
    return False


def _is_credential(path, value, registry):
    if _path_is_credential(path, registry):
        return True
    if registry["credentials"].get("value_scan") == "secrets" and isinstance(value, str):
        return bool(scan_for_secrets(value))
    return False


@pytest.mark.parametrize("path", [
    "admin-ui.token",
    "admin-ui.token-file",
    "variables.API_TOKEN",
    "variables.MY_SECRET",
    "credentials.private-key",
])
def test_c_credential_patterns_match(path):
    assert _is_credential(path, None, _registry()) is True


def test_c_a_secret_value_marks_the_path_even_without_a_credential_name():
    value = "ghp_" + "a" * 36
    assert scan_for_secrets(value), "fixture value must be reported by scan_for_secrets"
    assert _is_credential("variables.SOME_NEUTRAL_NAME", value, _registry()) is True


@pytest.mark.parametrize("path", [
    "max-tokens-overrides",
    "admin-ui.bind-host",
    "viz.port",
    "variables.PROJECT_NAME",
])
def test_c_non_credential_paths_do_not_match(path):
    assert _is_credential(path, None, _registry()) is False


def test_c_max_tokens_overrides_is_not_a_segment_match():
    value = _registry()["credentials"]["name_patterns"][0]
    assert re.search(value, "max-tokens-overrides", re.IGNORECASE) is None


# ------------------------------------------------------------- (d) registry

def test_d_registry_loads_softly(tmp_path):
    """A missing/malformed registry never crashes the doctor (behaves as before)."""
    from lib.doctor_detectors import _runtime_reader_keys

    class _FakeEnv:
        def __init__(self):
            self.agent_meta_root = tmp_path
            self.shared: dict = {}

    assert _runtime_reader_keys(_FakeEnv()) == set()          # missing
    (tmp_path / "config").mkdir()
    registry = tmp_path / "config" / "runtime-config-readers.yaml"
    registry.write_text("[unclosed", encoding="utf-8")
    assert _runtime_reader_keys(_FakeEnv()) == set()          # malformed
    registry.write_text("registry-version: 1\nreaders:\n  - {key: only-key}\n", encoding="utf-8")
    assert _runtime_reader_keys(_FakeEnv()) == {"only-key"}


def test_d_registry_shape():
    registry = _registry()
    assert registry["registry-version"] == 1
    readers = registry["readers"]
    assert readers, "registry has no readers"
    for entry in readers:
        assert entry.get("key"), entry
        assert entry.get("reader"), entry
        assert entry.get("effect"), entry
        assert (_ROOT / str(entry["reader"])).is_file(), entry

    keys = _reader_keys()
    assert len(keys) == len(set(keys)), f"duplicate reader keys: {keys}"

    registered = _registered_reader_files()
    assert {"scripts/admin-server.py", "scripts/lifecycle_check.py"} <= registered
    assert {"hooks/1-generic/repo-containment-impl.sh",
            "hooks/1-generic/orchestrator-guard-impl.sh",
            "hooks/1-generic/dod-push-check.sh"} <= registered
