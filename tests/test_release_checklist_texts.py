"""Text assertions for the release-checklist slash commands and their docs.

These are static content contracts: the commands are prompts, not code, so the
only observable behaviour is their own wording and the documentation rows that
advertise them. Covers AC-REL-10 (``/release-check`` is a check-only dry run
that delegates to the ``release`` agent and forbids every side effect) and the
two command entries in ``docs/api/slash-commands.md`` and ``README.md``.
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
