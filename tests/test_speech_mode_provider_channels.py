"""Issue #1300 task 1: speech-mode text source + provider-aware file channel."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.rules import load_speech_rule_text, sync_speech_mode  # noqa: E402

TARGET = Path(".claude/rules/speech-mode.md")


def _run(tmp_path, mode, provider_config=None):
    log = SyncLog()
    sync_speech_mode(REPO_ROOT, tmp_path, {"speech-mode": mode}, log, False,
                     provider_config=provider_config)
    return log


def test_has_rules_false_never_touches_rules_dir(tmp_path):  # AC-2
    _run(tmp_path, "caveman", {"has_rules": False})
    assert not (tmp_path / ".claude").exists()
    stale = tmp_path / TARGET
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    _run(tmp_path, "full", {"has_rules": False})  # OF-2: no cleanup
    assert stale.read_text(encoding="utf-8") == "old"


def test_has_rules_true_file_byte_identical(tmp_path):  # AC-3
    expected = (REPO_ROOT / "speech" / "caveman.md").read_bytes()
    _run(tmp_path, "caveman", {"has_rules": True})
    assert (tmp_path / TARGET).read_bytes() == expected
    other = tmp_path / "b"
    other.mkdir()
    _run(other, "caveman")  # default None = legacy behaviour
    assert (other / TARGET).read_bytes() == expected


def test_full_returns_none(tmp_path):  # AC-4
    assert load_speech_rule_text(REPO_ROOT, {"speech-mode": "full"}, SyncLog()) is None
    assert load_speech_rule_text(REPO_ROOT, {}, SyncLog()) is None


def test_missing_source_warns_without_crash(tmp_path):  # AC-6
    log = SyncLog()
    assert load_speech_rule_text(REPO_ROOT, {"speech-mode": "nope-xyz"}, log) is None
    assert any("nope-xyz" in str(w) for w in log.warnings)
    _run(tmp_path, "nope-xyz", {"has_rules": True})
    assert not (tmp_path / TARGET).exists()


def test_load_returns_source_text():
    text = load_speech_rule_text(REPO_ROOT, {"speech-mode": "caveman"}, SyncLog())
    assert text == (REPO_ROOT / "speech" / "caveman.md").read_text(encoding="utf-8")


def _block(mode, provider="Opencode"):
    from lib.config import build_variables, load_config
    from lib.context import _build_managed_block
    from lib.providers import load_providers_config

    config = dict(load_config(REPO_ROOT / ".meta-config" / "project.yaml"))
    config["speech-mode"] = mode
    variables, _ = build_variables(config, REPO_ROOT)
    variables.setdefault("PIPELINE_DETAILS_DIR", ".opencode/pipeline-details")
    return _build_managed_block(
        REPO_ROOT, config, variables, SyncLog(), provider=provider,
        provider_config=load_providers_config(REPO_ROOT), project_root=REPO_ROOT,
        active_set=frozenset(),
    )


def test_embed_speech_in_block_after_rules():  # AC-1
    block = _block("caveman")
    text = (REPO_ROOT / "speech" / "caveman.md").read_text(encoding="utf-8").strip("\n")
    assert "## Speech-Mode\n\n" + text in block
    assert block.index("## Regeln") < block.index("## Speech-Mode")
    assert block.index("## Speech-Mode") < block.index("managed-end")


def test_embed_idempotent_and_mode_switch_removes():  # AC-5, AC-4
    assert _block("caveman") == _block("caveman")
    full = _block("full")
    assert "## Speech-Mode" not in full
    assert "Kommunikationsstil" not in full


def _pipeline(tmp_path, provider):
    import subprocess
    (tmp_path / ".meta-config").mkdir()
    cfg = tmp_path / ".meta-config" / "project.yaml"
    cfg.write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        f"ai-providers:\n- {provider}\nspeech-mode: caveman\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: t\n  PROJECT_PREFIX: t\n"
        "  AGENT_META_REPO: example/agent-meta\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    r = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "sync.py"),
                        "--config", str(cfg), "--init"], cwd=tmp_path,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]


def test_pipeline_has_rules_false_writes_no_speech_rule(tmp_path):  # AC-2
    _pipeline(tmp_path, "Opencode")
    assert not (tmp_path / TARGET).exists()


def test_pipeline_has_rules_true_writes_speech_rule(tmp_path):  # AC-3
    _pipeline(tmp_path, "Claude")
    assert (tmp_path / TARGET).read_bytes() == (REPO_ROOT / "speech" / "caveman.md").read_bytes()
