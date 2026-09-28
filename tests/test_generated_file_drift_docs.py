"""W3-5 — the docs-consolidation half of the generated-file drift store.

Covers IC-16 / AC-19 / AC-37 / NFA-05: the hybrid doc files and the two
generated index files join the hash baseline, with three properties that make
the store safe for them:

* **Marker body only.** ``README.md`` (and ``llms.txt``, ``ARCHITECTURE.md``)
  are hand prose *plus* generated regions. Hashing the whole file would report
  every prose edit as drift, so only the extracted marker body is hashed, under
  the store key ``<rel>#docs:<region>`` (IC-16, decision A8).
* **The composite key never reaches the filesystem.** ``README.md#docs:facts``
  is a store key, not a path. ``backup_drifted_files()`` must stay fail-soft
  on it: no ``README.md#docs:facts`` file and no ``.sync-backup-*`` sibling is
  created (AC-19d, NFA-05).
* **The allowlist matches the base path.** ``fnmatch`` runs against the whole
  string, so a pattern ``README.md`` does *not* match
  ``README.md#docs:facts`` — which would make every allowlist entry for a doc
  host silently ineffective. IC-16 (M8) therefore makes base-path matching
  mandatory; AC-37 pins it.

The drift store is **provider-independent** for these keys, exactly like the
existing ``PLATFORM_DEFAULTS_RESOLVED_REL`` pseudo-provider, so the docs paths
stay out of ``_iter_managed_files()`` (which is provider-scoped and would
misattribute a doc file to a provider).

Two tests below deliberately cross a module boundary instead of restating a
contract. ``test_drift_store_hashes_the_body_the_renderer_actually_writes``
renders through the real ``doc_renderer.apply_fact_blocks()``, so the marker
syntax is owned by ``doc_renderer`` and not copied into this file — without it
the marker strings below are a second, unverified source of truth.
``test_allowlist_hint_in_the_drift_warning_suppresses_the_finding`` parses the
string out of the real ``sync_pipeline`` warning and pastes it into a real
allowlist, so the message cannot name an entry that suppresses nothing.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from scripts.lib.doc_renderer import (
    REGION_FACT_KEYS,
    apply_fact_blocks,
    render_doc_fact_block,
)
from scripts.lib.generated_file_drift import (
    DOCS_FACT_BLOCK_HOSTS,
    DOCS_GENERATED_RELS,
    DOCS_MARKER_KEY_SUFFIX,
    _iter_managed_files,
    _load_hashes,
    _normalize_marker_body,
    backup_drifted_files,
    base_path_for_key,
    capture_generated_file_hashes,
    content_hash,
    is_allowlisted,
    scan_generated_file_drift,
)
from scripts.lib.log import SyncLog

# cli_commands / sync_pipeline use absolute `from lib.xxx import ...` imports,
# so `lib` must be importable as a top-level package -- same bootstrap as
# tests/test_generated_file_drift_pipeline_wiring.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.lib.sync_pipeline import _sync_stage_generated_file_drift_scan

#: The pseudo-provider every docs finding carries (IC-16).
DOCS_PROVIDER = "docs-consolidation"

#: The store key AC-19 names literally.
FACTS_KEY = "README.md" + DOCS_MARKER_KEY_SUFFIX + "facts"

_GENERATED_BODY = "| Fact | Value |\n|---|---|\n| Agents | 3 |"
_HAND_EDITED_BODY = "| Fact | Value |\n|---|---|\n| Agents | 999 |"

_PROSE_BEFORE = "# Project\n\nHand-written intro paragraph.\n"
_PROSE_AFTER = "# Project\n\nHand-written intro paragraph, reworded by a human.\n"


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _readme(body: str = _GENERATED_BODY, prose: str = _PROSE_BEFORE) -> str:
    """A hybrid doc file: hand prose plus one generated ``facts`` region."""
    return (
        f"{prose}\n"
        f"<!-- agent-meta:docs-begin facts -->\n"
        f"{body}\n"
        f"<!-- agent-meta:docs-end facts -->\n"
        "\n## Hand-written section\n\nMore prose, never generated.\n"
    )


def _provider_config() -> dict:
    return {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}


def _capture(project_root: Path, agent_meta_root: Path, provider_config: dict) -> None:
    capture_generated_file_hashes(
        agent_meta_root, project_root, {}, provider_config, False,
    )


def _scan(project_root: Path, agent_meta_root: Path, provider_config: dict) -> list[dict]:
    return scan_generated_file_drift(agent_meta_root, project_root, {}, provider_config)


def _only(findings: list[dict], store_key: str) -> dict:
    """The single finding for *store_key*, asserted to be exactly one."""
    matching = [f for f in findings if f["path"] == store_key]
    assert len(matching) == 1, (
        f"expected exactly one finding for {store_key!r}, got {matching} "
        f"in {findings}"
    )
    return matching[0]


def _baselined_readme(tmp_path: Path, **kwargs) -> tuple[Path, Path, dict]:
    """A project whose README carries a generated region and a fresh baseline."""
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    _write(project_root, "README.md", _readme(**kwargs))
    _capture(project_root, agent_meta_root, provider_config)
    return agent_meta_root, project_root, provider_config


# ---------------------------------------------------------------------------
# Store-key shape
# ---------------------------------------------------------------------------


def test_docs_constants_match_the_ic16_contract() -> None:
    assert DOCS_GENERATED_RELS == ("docs/INDEX.md", "docs/architecture/INDEX.md")
    assert DOCS_FACT_BLOCK_HOSTS == ("README.md", "llms.txt", "ARCHITECTURE.md")
    assert DOCS_MARKER_KEY_SUFFIX == "#docs:"


def test_capture_stores_the_marker_body_under_the_composite_key(tmp_path: Path) -> None:
    _agent_meta_root, project_root, _pc = _baselined_readme(tmp_path)

    hashes = _load_hashes(project_root)
    assert FACTS_KEY in hashes, sorted(hashes)
    assert hashes[FACTS_KEY] == content_hash(_GENERATED_BODY)


def test_capture_never_stores_the_whole_host_file(tmp_path: Path) -> None:
    """The prose half of a hybrid doc file is not drift-tracked at all."""
    _agent_meta_root, project_root, _pc = _baselined_readme(tmp_path)

    assert "README.md" not in _load_hashes(project_root)


def test_base_path_for_key_strips_only_the_marker_suffix() -> None:
    assert base_path_for_key(FACTS_KEY) == "README.md"
    assert base_path_for_key("docs/INDEX.md") == "docs/INDEX.md"


# ---------------------------------------------------------------------------
# AC-19 (a)+(b) — marker body only
# ---------------------------------------------------------------------------


def test_marker_body_only(tmp_path: Path) -> None:
    """AC-19: a prose edit is silent, a region edit is reported.

    This is the one test that carries both halves of the acceptance criterion,
    because they only mean something together: the *same* file, the *same*
    baseline, one edit in the hand prose and one edit inside the marker.
    """
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)

    # (a) hand prose is not drift-relevant.
    _write(project_root, "README.md", _readme(prose=_PROSE_AFTER))
    prose_findings = _scan(project_root, agent_meta_root, provider_config)
    assert [f for f in prose_findings if f["path"] == FACTS_KEY] == [], prose_findings

    # (b) the marker body is.
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    region_findings = _scan(project_root, agent_meta_root, provider_config)
    assert _only(region_findings, FACTS_KEY)["provider"] == DOCS_PROVIDER


def test_prose_edit_alone_produces_no_finding_at_all(tmp_path: Path) -> None:
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)

    _write(project_root, "README.md", _readme(prose=_PROSE_AFTER))

    assert _scan(project_root, agent_meta_root, provider_config) == []


def test_normalized_marker_body_ignores_trailing_whitespace(tmp_path: Path) -> None:
    """IC-16's normalization: trailing spaces are not a semantic change."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    padded = "\n".join(f"{line}   " for line in _GENERATED_BODY.splitlines())

    _write(project_root, "README.md", _readme(body=padded))

    assert _scan(project_root, agent_meta_root, provider_config) == []


def test_leading_and_trailing_blank_lines_in_the_body_are_normalized(
    tmp_path: Path,
) -> None:
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)

    _write(project_root, "README.md", _readme(body=f"\n\n{_GENERATED_BODY}\n\n"))

    assert _scan(project_root, agent_meta_root, provider_config) == []


# ---------------------------------------------------------------------------
# AC-19 (d) + NFA-05 — the composite key must not become a path
# ---------------------------------------------------------------------------


def test_no_backup_for_hash_key(tmp_path: Path) -> None:
    """AC-19(d): a ``#docs:`` finding is reported, never materialized.

    ``Path("README.md#docs:facts")`` is a perfectly legal filename on POSIX, so
    this is a real risk, not a theoretical one: without an explicit guard, a
    host that happens to carry a file of the composite name would get a
    ``.sync-backup-*`` sibling written next to it.
    """
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    # Decoy: a real file occupying exactly the composite store key. The guard
    # must key off the KEY, not off whether the read happens to succeed.
    _write(project_root, FACTS_KEY, "decoy content\n")
    findings = _scan(project_root, agent_meta_root, provider_config)
    _only(findings, FACTS_KEY)

    backups = backup_drifted_files(findings, project_root, _NullLog())

    assert backups == []
    assert (project_root / FACTS_KEY).read_text(encoding="utf-8") == "decoy content\n"
    assert list(project_root.glob("*#docs:*")) == [project_root / FACTS_KEY]
    assert list(project_root.rglob("*.sync-backup-*")) == []


def test_drift_scan_stage_does_not_mutate_a_hand_edited_region(
    tmp_path: Path,
) -> None:
    """NFA-05 as far as the drift store owns it: report, never rewrite.

    A ``#docs:`` key cannot be backed up, so the store must not touch the file
    either — the edit has to survive for the human to resolve.
    """
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    before = (project_root / "README.md").read_text(encoding="utf-8")

    findings = _scan(project_root, agent_meta_root, provider_config)
    backup_drifted_files(findings, project_root, _NullLog())

    assert (project_root / "README.md").read_text(encoding="utf-8") == before
    assert _HAND_EDITED_BODY in before


# ---------------------------------------------------------------------------
# AC-37 — the allowlist matches the base path
# ---------------------------------------------------------------------------


def test_allowlist_matches_base_path(tmp_path: Path) -> None:
    """AC-37: ``allow-edits: ["README.md"]`` suppresses the region drift.

    Without base-path matching this finding survives, because ``fnmatch`` runs
    against the whole ``README.md#docs:facts`` string (IC-16, M8).
    """
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    _write(
        project_root,
        ".meta-config/drift-allowlist.yaml",
        'allow-edits:\n  - "README.md"\n',
    )

    findings = _scan(project_root, agent_meta_root, provider_config)

    assert [f for f in findings if f["path"] == FACTS_KEY] == [], findings


def test_is_allowlisted_matches_a_composite_key_against_its_base_path() -> None:
    assert is_allowlisted(FACTS_KEY, ["README.md"])
    assert is_allowlisted(FACTS_KEY, ["*.md"])


def test_allowlist_entry_for_another_host_does_not_suppress_this_one(
    tmp_path: Path,
) -> None:
    """Base-path matching must not become match-anything."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    _write(
        project_root,
        ".meta-config/drift-allowlist.yaml",
        'allow-edits:\n  - "llms.txt"\n',
    )

    findings = _scan(project_root, agent_meta_root, provider_config)

    assert FACTS_KEY in [f["path"] for f in findings]


def test_allowlisted_hand_prose_still_produces_no_finding(tmp_path: Path) -> None:
    """AC-37, second half: the prose is not hashed, so it cannot be reported."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(
        project_root,
        ".meta-config/drift-allowlist.yaml",
        'allow-edits:\n  - "README.md"\n',
    )
    _write(project_root, "README.md", _readme(prose=_PROSE_AFTER))

    assert _scan(project_root, agent_meta_root, provider_config) == []


# ---------------------------------------------------------------------------
# The two generated index files — whole-file hashing, no marker key
# ---------------------------------------------------------------------------


def test_generated_index_file_is_hashed_whole(tmp_path: Path) -> None:
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    _write(project_root, "docs/INDEX.md", "# Documentation Index\n\n- [a](a.md)\n")
    _capture(project_root, agent_meta_root, provider_config)

    assert _load_hashes(project_root)["docs/INDEX.md"] == content_hash(
        "# Documentation Index\n\n- [a](a.md)\n"
    )

    _write(project_root, "docs/INDEX.md", "# Documentation Index\n\n- [a](a.md)\n- [b](b.md)\n")
    findings = _scan(project_root, agent_meta_root, provider_config)

    assert _only(findings, "docs/INDEX.md") == {
        "path": "docs/INDEX.md",
        "provider": DOCS_PROVIDER,
    }


def test_missing_generated_index_file_produces_no_key_and_no_finding(
    tmp_path: Path,
) -> None:
    """``docs/INDEX.md`` lands in W3-6 — its absence is not drift."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)

    assert "docs/INDEX.md" not in _load_hashes(project_root)
    assert _scan(project_root, agent_meta_root, provider_config) == []


def test_second_generated_index_rel_is_tracked_too(tmp_path: Path) -> None:
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    _write(project_root, "docs/architecture/INDEX.md", "# Architecture\n")
    _capture(project_root, agent_meta_root, provider_config)

    assert "docs/architecture/INDEX.md" in _load_hashes(project_root)


def test_every_fact_block_host_can_carry_a_region(tmp_path: Path) -> None:
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    for rel in DOCS_FACT_BLOCK_HOSTS:
        _write(project_root, rel, _readme())
    _capture(project_root, agent_meta_root, provider_config)

    hashes = _load_hashes(project_root)
    for rel in DOCS_FACT_BLOCK_HOSTS:
        assert f"{rel}{DOCS_MARKER_KEY_SUFFIX}facts" in hashes, sorted(hashes)


def test_multiple_regions_in_one_host_get_one_key_each(tmp_path: Path) -> None:
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    _write(project_root, "README.md", _readme() + _region("roster", "- developer"))
    _capture(project_root, agent_meta_root, provider_config)

    assert FACTS_KEY in _load_hashes(project_root)
    assert "README.md" + DOCS_MARKER_KEY_SUFFIX + "roster" in _load_hashes(project_root)


# ---------------------------------------------------------------------------
# Symmetry, and the provider-independence boundary
# ---------------------------------------------------------------------------


def test_scan_and_capture_are_symmetric(tmp_path: Path) -> None:
    """A fresh capture must leave the next scan silent, or drift is permanent."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "docs/INDEX.md", "# Documentation Index\n")

    _capture(project_root, agent_meta_root, provider_config)
    after_capture = _scan(project_root, agent_meta_root, provider_config)

    assert after_capture == [], after_capture


def test_capture_is_a_noop_in_dry_run(tmp_path: Path) -> None:
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write(project_root, "README.md", _readme())

    capture_generated_file_hashes(
        agent_meta_root, project_root, {}, _provider_config(), True,
    )

    assert not (project_root / ".meta-config" / "generated-file-hashes.json").exists()


def test_docs_paths_do_not_enter_iter_managed_files(tmp_path: Path) -> None:
    """IC-16: provider-scoped walking would misattribute a doc file."""
    project_root = tmp_path / "project"
    _write(project_root, "README.md", _readme())
    _write(project_root, "docs/INDEX.md", "# Documentation Index\n")
    _write(project_root, ".claude/agents/developer.md", "generated\n")
    _write(project_root, ".claude/agents/.agent-meta-managed", "developer.md\n")

    files = _iter_managed_files(
        tmp_path / "agent-meta", project_root, "Claude", _provider_config()["Claude"], {},
    )

    assert [p.relative_to(project_root).as_posix() for p in files] == [
        ".claude/agents/developer.md",
    ]


def test_docs_findings_carry_no_provider_name(tmp_path: Path) -> None:
    """The pseudo-provider is the only attribution: docs are not a provider."""
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))

    providers = {f["provider"] for f in _scan(project_root, agent_meta_root, provider_config)}

    assert providers == {DOCS_PROVIDER}
    assert providers.isdisjoint(provider_config)


# ---------------------------------------------------------------------------
# Cross-module invariants — the two contracts a copy cannot hold
# ---------------------------------------------------------------------------


def _render_facts(agents: str) -> dict[str, str]:
    """The one fact the README fixture's ``facts`` region renders."""
    return {
        REGION_FACT_KEYS["facts"]: f"| Fact | Value |\n|---|---|\n| Agents | {agents} |",
    }


def test_drift_store_hashes_the_body_the_renderer_actually_writes(
    tmp_path: Path,
) -> None:
    """The tie between ``doc_renderer`` and the drift store (F3).

    Every other test in this module builds its hybrid file out of hand-written
    marker strings, so the marker syntax is a **second source of truth**: change
    it in ``DOCS_BLOCK_RE`` and only ``_docs_marker_bodies()`` and the renderer
    would move together, while these fixtures silently stop matching anything.
    Rendering through the real ``apply_fact_blocks()`` removes the copy — the
    markers this test sees are the ones the writer actually emits.

    Three assertions, each falsifiable on its own:

    1. the store hashes the rendered body under the composite key;
    2. a capture straight after a render leaves the next scan silent, so a
       real render can never manufacture permanent drift;
    3. a re-render with different facts is reported **on that same key** —
       which it cannot be if the store extracted no region at all.
    """
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    provider_config = _provider_config()
    facts = _render_facts("42")

    _write(project_root, "README.md", apply_fact_blocks(_readme(), facts))
    _capture(project_root, agent_meta_root, provider_config)

    assert _load_hashes(project_root)[FACTS_KEY] == content_hash(
        _normalize_marker_body(render_doc_fact_block("facts", facts))
    )
    assert _scan(project_root, agent_meta_root, provider_config) == []

    _write(
        project_root,
        "README.md",
        apply_fact_blocks(_readme(), _render_facts("43")),
    )

    assert _only(
        _scan(project_root, agent_meta_root, provider_config), FACTS_KEY,
    )["provider"] == DOCS_PROVIDER


#: Wording-tolerant on purpose: the assertion below is about whether the named
#: entry *works*, so a reworded message must not be the only thing that can go
#: red here. ``Add it to ...`` parses to ``it`` and fails the semantics assert.
_HINT_RE = re.compile(r"Add (.+?) to \.meta-config/drift-allowlist\.yaml")


def _allowlist_hint(warning: str) -> str:
    """The allowlist entry the warning tells the user to paste, unquoted."""
    match = _HINT_RE.search(warning)
    assert match is not None, f"warning names no allowlist entry: {warning!r}"
    return match.group(1).strip("'\"")


def test_allowlist_hint_in_the_drift_warning_suppresses_the_finding(
    tmp_path: Path,
) -> None:
    """The warning's copy-paste string has to actually work (F2).

    The message prints the store key ``README.md#docs:facts``, but the allowlist
    is matched against the **base path** (``is_allowlisted()`` runs fnmatch over
    ``base_path_for_key()``), so pasting the printed key suppressed nothing —
    exactly the silent failure the base-path rule exists to prevent. The hint
    therefore names the base path while the full key stays in the message for
    identification; pasting the key verbatim must remain useless, so this test
    pins both halves.
    """
    agent_meta_root, project_root, provider_config = _baselined_readme(tmp_path)
    _write(project_root, "README.md", _readme(body=_HAND_EDITED_BODY))
    log = SyncLog()

    _sync_stage_generated_file_drift_scan(
        agent_meta_root, project_root, {}, provider_config,
        argparse.Namespace(dry_run=False), log,
    )

    assert len(log.warnings) == 1, log.warnings
    warning = log.warnings[0]
    assert FACTS_KEY in warning, warning
    suggested = _allowlist_hint(warning)

    assert suggested == base_path_for_key(FACTS_KEY) == "README.md", warning
    assert is_allowlisted(FACTS_KEY, [suggested]), warning
    assert not is_allowlisted(FACTS_KEY, [FACTS_KEY]), (
        "the full store key must NOT be a working allowlist entry -- that is the "
        "bug this hint shape avoids"
    )

    _write(
        project_root,
        ".meta-config/drift-allowlist.yaml",
        f'allow-edits:\n  - "{suggested}"\n',
    )

    assert _scan(project_root, agent_meta_root, provider_config) == []


# ---------------------------------------------------------------------------
# helpers local to this module
# ---------------------------------------------------------------------------


def _region(region: str, body: str) -> str:
    return (
        f"<!-- agent-meta:docs-begin {region} -->\n"
        f"{body}\n"
        f"<!-- agent-meta:docs-end {region} -->\n"
    )


class _NullLog:
    """The slice of ``SyncLog`` that ``backup_drifted_files`` touches."""

    def __init__(self) -> None:
        self.debugs: list[tuple[str, str]] = []

    def debug(self, channel: str, message: str) -> None:
        self.debugs.append((channel, message))
