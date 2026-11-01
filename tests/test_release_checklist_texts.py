"""Text assertions for the release-checklist slash commands and their docs.

These are static content contracts: the commands are prompts, not code, so the
only observable behaviour is their own wording and the documentation rows that
advertise them. Covers AC-REL-10 (``/release-check`` is a check-only dry run
that delegates to the ``release`` agent and forbids every side effect), AC-REL-16
(the manager recipe) and AC-REL-20 (the ``docs/RELEASE_GATES.md`` checklist-mode
section, the ``[Unreleased]`` changelog entry and the commented example in
``howto/configs/project.yaml.example``), plus the two command entries in
``docs/api/slash-commands.md`` and ``README.md``.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_check_command():                                           # AC-REL-10
    t = (REPO_ROOT / "commands/1-generic/release-check.md").read_text(encoding="utf-8")
    assert t.startswith("---\ndescription:") and "MODE: check-only" in t
    for forbidden in ("tag", "push", "build", "version bump", "edit", "commit", "gh release"):
        assert forbidden in t.lower()
    assert "not active" in t.lower()                                        # Release-Agent inaktiv => Hinweis


def test_set_release_checklist_command():
    t = (REPO_ROOT / "commands/1-generic/set-release-checklist.md").read_text(encoding="utf-8")
    assert "release-checklist" in t and "quote" in t and "--validate" in t


def test_commands_documented():
    for p in ("docs/api/slash-commands.md", "README.md"):
        s = (REPO_ROOT / p).read_text(encoding="utf-8")
        assert "/release-check" in s and "/set-release-checklist" in s


def test_manager_recipe():                                                  # AC-REL-16
    t = (REPO_ROOT / "agents/1-generic/agent-meta-manager.md").read_text(encoding="utf-8")
    assert 'version: "1.26.0"' in t and "### 14d." in t and "release-checklist" in t
    sec3 = t.split("## 3. Confirmation required", 1)[1].split("## 4.", 1)[0]
    assert "release-checklist.mode" in sec3 and "strict" in sec3
    assert "gates stay hard in every mode" in t.lower()
    assert "weicher" not in t and "softer" not in t.lower()                 # U8: kein "Gates werden weicher"
    assert "quote" in t.lower()


def test_release_gates_doc():                                               # AC-REL-20
    t = (REPO_ROOT / "docs/RELEASE_GATES.md").read_text(encoding="utf-8")
    sec = t.split("## Checklist-Modus", 1)[1]
    for phrase in ("off", "advisory", "strict", "Gates bleiben in jedem Modus hart", "seiteneffektfrei",
                   "Prompt-/Konventions-Boundary", "--release-check", "Hook", "access: read"):
        assert phrase in sec, phrase

def test_changelog_and_example():
    cl = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("## [2.0.0-beta.5]", 1)[0]
    assert "release-checklist" in cl and "advisory" in cl and "strict" in cl and "Prompt" in cl
    assert "release-checklist:" in (REPO_ROOT / "howto/configs/project.yaml.example").read_text(encoding="utf-8")
